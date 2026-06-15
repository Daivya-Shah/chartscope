"""PHI de-identification via Microsoft Presidio."""

from __future__ import annotations

import logging
import re
from typing import Any

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, RecognizerResult

logger = logging.getLogger(__name__)

_analyzer: AnalyzerEngine | None = None
_anonymizer: AnonymizerEngine | None = None
_presidio_model: str | None = None

# Typed replacement tags for HIPAA Safe Harbor identifiers + custom types.
ENTITY_TAGS: dict[str, str] = {
    "PERSON": "[NAME]",
    "DATE_TIME": "[DATE]",
    "PHONE_NUMBER": "[PHONE]",
    "EMAIL_ADDRESS": "[EMAIL]",
    "LOCATION": "[LOCATION]",
    "US_SSN": "[SSN]",
    "US_DRIVER_LICENSE": "[ID]",
    "US_PASSPORT": "[ID]",
    "US_BANK_NUMBER": "[ACCOUNT]",
    "CREDIT_CARD": "[ACCOUNT]",
    "IP_ADDRESS": "[IP]",
    "MRN": "[MRN]",
    "ACCOUNT_NUMBER": "[ACCOUNT]",
    "AGE_OVER_89": "[AGE>89]",
}

# Prefer lg for Presidio PHI recall; fall back to md if lg unavailable.
_PRESIDIO_MODEL_CANDIDATES = ("en_core_web_lg", "en_core_web_md", "en_core_web_sm")

# Ages under 90 (HIPAA Safe Harbor) — preserve when Presidio mis-tags as DATE_TIME.
_AGE_YEARS_OLD = re.compile(r"\b(\d{1,2})\s*-?\s*year\s*-?\s*old\b", re.IGNORECASE)
_AGE_YO = re.compile(r"\b(\d{1,2})\s*(yo|y/o|yof|yom)\b", re.IGNORECASE)

# Clinical durations — not PHI.
_NUMERIC_DURATION = re.compile(
    r"\b\d+\s*[- ]?\s*(?:year|month|week|day|hour)s?\b(?!\s*old)",
    re.IGNORECASE,
)
_WRITTEN_DURATION = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|couple|few|several)\s*"
    r"[- ]?\s*(?:year|month|week|day|hour)s?\b(?!\s*old)",
    re.IGNORECASE,
)

# Vague relative clinical time — not calendar PHI.
_VAGUE_RELATIVE = re.compile(
    r"^\s*(?:today|yesterday|currently|recently|now|presently|"
    r"this morning|this afternoon|this evening|this week|this month)\s*$",
    re.IGNORECASE,
)

# Medication dosing frequency — not calendar PHI.
_MED_FREQUENCY = re.compile(
    r"^\s*(?:daily|nightly|weekly|hourly|bid|tid|qid|qhs|prn)\s*$",
    re.IGNORECASE,
)

_PRESERVE_DATE_TIME_CHECKS: tuple[re.Pattern[str], ...] = (
    _NUMERIC_DURATION,
    _WRITTEN_DURATION,
    _VAGUE_RELATIVE,
    _MED_FREQUENCY,
)


def _resolve_presidio_model() -> str:
    import spacy

    for model_name in _PRESIDIO_MODEL_CANDIDATES:
        try:
            spacy.load(model_name)
            if model_name != "en_core_web_lg":
                logger.warning(
                    "Presidio using fallback spaCy model %s (en_core_web_lg preferred for PHI recall)",
                    model_name,
                )
            return model_name
        except OSError:
            continue
    raise OSError(
        "No spaCy model found for Presidio. Install with: "
        "python -m spacy download en_core_web_lg"
    )


def _build_custom_recognizers() -> list[PatternRecognizer]:
    mrn_recognizer = PatternRecognizer(
        supported_entity="MRN",
        name="mrn_recognizer",
        patterns=[
            Pattern(name="syn_mrn", regex=r"\bSYN-\d{4,6}\b", score=0.95),
            Pattern(name="mrn_inline", regex=r"\bMRN\s*:?\s*[A-Z0-9-]+\b", score=0.9),
            Pattern(name="record_number", regex=r"\b(?:Record|Medical Record)\s*#?\s*\d{4,}\b", score=0.85),
        ],
    )

    account_recognizer = PatternRecognizer(
        supported_entity="ACCOUNT_NUMBER",
        name="account_recognizer",
        patterns=[
            Pattern(
                name="account_hash",
                regex=r"\b(?:Account|Acct\.?|Member ID)\s*#?\s*[A-Z0-9-]{4,}\b",
                score=0.85,
            ),
            Pattern(name="numeric_account", regex=r"\bAccount\s*Number\s*:?\s*\d{6,}\b", score=0.85),
        ],
    )

    age_recognizer = PatternRecognizer(
        supported_entity="AGE_OVER_89",
        name="age_over_89_recognizer",
        patterns=[
            Pattern(
                name="age_years_old",
                regex=r"\b(9[0-9]|[1-9]\d{2,})\s*-?\s*year(?:s)?\s*-?\s*old\b",
                score=0.9,
            ),
            Pattern(
                name="aged_n",
                regex=r"\b(?:age[d]?|Age)\s*(?:of\s*)?(9[0-9]|[1-9]\d{2,})\b",
                score=0.85,
            ),
        ],
    )

    return [mrn_recognizer, account_recognizer, age_recognizer]


def _get_engines() -> tuple[AnalyzerEngine, AnonymizerEngine, str]:
    global _analyzer, _anonymizer, _presidio_model

    if _analyzer is not None and _anonymizer is not None and _presidio_model is not None:
        return _analyzer, _anonymizer, _presidio_model

    model_name = _resolve_presidio_model()
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": model_name}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(nlp_engine=nlp_engine, languages=["en"])
    for recognizer in _build_custom_recognizers():
        registry.add_recognizer(recognizer)

    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        registry=registry,
        supported_languages=["en"],
    )
    anonymizer = AnonymizerEngine()

    _analyzer = analyzer
    _anonymizer = anonymizer
    _presidio_model = model_name
    return analyzer, anonymizer, model_name


def _tag_for_entity(entity_type: str) -> str:
    return ENTITY_TAGS.get(entity_type, f"[{entity_type}]")


def _build_operators() -> dict[str, OperatorConfig]:
    operators: dict[str, OperatorConfig] = {}
    for entity_type, tag in ENTITY_TAGS.items():
        operators[entity_type] = OperatorConfig("replace", {"new_value": tag})
    return operators


def _is_preservable_age(span_text: str) -> bool:
    """Return True for ages under 90 (HIPAA Safe Harbor — not an identifier)."""
    for pattern in (_AGE_YEARS_OLD, _AGE_YO):
        match = pattern.search(span_text)
        if match:
            return int(match.group(1)) <= 89
    return False


def _should_preserve_date_time(span_text: str) -> bool:
    """Deny-list filter: reject DATE_TIME spans that are clinical ages/durations, not PHI."""
    if _is_preservable_age(span_text):
        return True
    return any(pattern.search(span_text) for pattern in _PRESERVE_DATE_TIME_CHECKS)


def _filter_date_time_false_positives(
    text: str,
    results: list[RecognizerResult],
) -> list[RecognizerResult]:
    """Drop DATE_TIME spans that match clinical age/duration/relative-time deny-list."""
    filtered: list[RecognizerResult] = []
    for result in results:
        if result.entity_type != "DATE_TIME":
            filtered.append(result)
            continue
        span_text = text[result.start : result.end]
        if _should_preserve_date_time(span_text):
            continue
        filtered.append(result)
    return filtered


def deidentify(text: str) -> dict[str, Any]:
    """Detect and mask PHI; returns clean_text, phi_spans, redaction_count."""
    if not text or not text.strip():
        return {"clean_text": "", "phi_spans": [], "redaction_count": 0}

    analyzer, anonymizer, _ = _get_engines()

    results: list[RecognizerResult] = analyzer.analyze(
        text=text,
        language="en",
        entities=list(ENTITY_TAGS.keys()),
    )

    # Drop overlapping lower-score spans (keep highest score per start position).
    results = sorted(results, key=lambda r: (-r.score, r.start))
    kept: list[RecognizerResult] = []
    occupied: list[tuple[int, int]] = []
    for result in results:
        if any(not (result.end <= start or result.start >= end) for start, end in occupied):
            continue
        kept.append(result)
        occupied.append((result.start, result.end))

    kept = _filter_date_time_false_positives(text, kept)

    operators = _build_operators()
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=kept,
        operators=operators,
    )

    phi_spans = [
        {
            "type": r.entity_type,
            "start": r.start,
            "end": r.end,
            "text": text[r.start : r.end],
        }
        for r in kept
    ]

    return {
        "clean_text": anonymized.text,
        "phi_spans": phi_spans,
        "redaction_count": len(kept),
    }
