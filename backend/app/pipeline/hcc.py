"""HCC V28 coding-gap detection via hccinfhir."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "CMS-HCC Model V28"
FALLBACK_MODELS = [
    "CMS-HCC Model V28",
    "CMS-HCC Model V24",
    "CMS-HCC Model V22",
]
DEFAULT_AGE = 70
DEFAULT_SEX = "M"
LINK_THRESHOLD = float(os.getenv("CHARTSCOPE_LINK_THRESHOLD", "0.55"))
PREFERRED_SECTIONS = {"ASSESSMENT", "PLAN", "ASSESSMENT AND PLAN"}

_hcc_engine: Any | None = None
_icd_hcc_cache: dict[tuple[str, int, str], list[dict[str, str]]] = {}

_AGE_PATTERNS = (
    re.compile(r"\b(\d{1,3})\s*[-\s]?\s*(?:year|yr|yo|y/o|y\.o\.)\s*[-\s]?\s*old\b", re.I),
    re.compile(r"\b(\d{1,3})\s*(?:yo|y/o|y\.o\.)\b", re.I),
)
_SEX_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(?:\d{1,3}\s*[-\s]?)?(?:year|yr|yo|y/o|y\.o\.)?\s*[-\s]?old\s+(male|female)\b", re.I), ""),
    (re.compile(r"\b(male|female)\b", re.I), ""),
    (re.compile(r"\b(man|woman|boy|girl)\b", re.I), ""),
)


def _normalize_icd10(code: str) -> str:
    return code.strip().upper().replace(" ", "")


def _sex_token_to_mf(token: str) -> str:
    t = token.lower()
    if t in {"male", "man", "boy", "m"}:
        return "M"
    if t in {"female", "woman", "girl", "f"}:
        return "F"
    return DEFAULT_SEX


def demographics_from_text(text: str) -> dict[str, int | str]:
    """Parse age and sex from clinical note text."""
    age = DEFAULT_AGE
    sex = DEFAULT_SEX

    for pattern in _AGE_PATTERNS:
        match = pattern.search(text)
        if match:
            parsed = int(match.group(1))
            if 0 < parsed <= 120:
                age = parsed
                break

    for pattern, _ in _SEX_PATTERNS:
        match = pattern.search(text)
        if match:
            sex = _sex_token_to_mf(match.group(1))
            break

    return {"age": age, "sex": sex}


def _get_hcc_engine() -> Any:
    global _hcc_engine
    if _hcc_engine is not None:
        return _hcc_engine

    from hccinfhir import HCCInFHIR

    last_error: Exception | None = None
    for model_name in FALLBACK_MODELS:
        try:
            _hcc_engine = HCCInFHIR(model_name=model_name)
            logger.info("Initialized hccinfhir engine: %s", model_name)
            return _hcc_engine
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load HCC model %s: %s", model_name, exc)
            last_error = exc

    raise RuntimeError("Could not initialize hccinfhir HCC engine") from last_error


def _demographics_dict(age: int, sex: str) -> dict[str, int | str]:
    return {"age": age, "sex": sex}


def calculate_raf(
    icd10_codes: list[str],
    age: int,
    sex: str,
) -> tuple[float, list[str], dict[str, Any]]:
    """Return (risk_score, final_hcc_list, full RAFResult as dict-like fields)."""
    engine = _get_hcc_engine()
    codes = [_normalize_icd10(c) for c in icd10_codes if c and c.strip()]
    result = engine.calculate_from_diagnosis(codes, demographics=_demographics_dict(age, sex))
    return float(result.risk_score), list(result.hcc_list), result


def _hcc_label_map(result: Any) -> dict[str, str]:
    labels: dict[str, str] = {}
    for detail in result.hcc_details or []:
        labels[str(detail.hcc)] = str(detail.label)
    return labels


def map_icd10_to_hccs(icd10: str, age: int, sex: str) -> list[dict[str, str]]:
    """Map a single ICD-10 code to contributing HCC categories (cached)."""
    code = _normalize_icd10(icd10)
    cache_key = (code, age, sex)
    if cache_key in _icd_hcc_cache:
        return _icd_hcc_cache[cache_key]

    engine = _get_hcc_engine()
    result = engine.calculate_from_diagnosis([code], demographics=_demographics_dict(age, sex))
    mapped: list[dict[str, str]] = []
    labels = _hcc_label_map(result)

    if result.hcc_details:
        for detail in result.hcc_details:
            mapped.append({"hcc": str(detail.hcc), "label": str(detail.label)})
    elif result.hcc_list:
        for hcc in result.hcc_list:
            mapped.append({"hcc": str(hcc), "label": labels.get(str(hcc), f"HCC {hcc}")})

    _icd_hcc_cache[cache_key] = mapped
    return mapped


def _section_priority(section: str | None) -> int:
    if not section:
        return 0
    normalized = section.strip().upper()
    if normalized in PREFERRED_SECTIONS:
        return 3
    if "ASSESSMENT" in normalized or "PLAN" in normalized:
        return 2
    return 1


def _build_evidenced_codes(
    active_problem_entities: list[dict[str, Any]],
    link_threshold: float = LINK_THRESHOLD,
) -> dict[str, dict[str, Any]]:
    """Select evidenced ICD-10 codes from linked active problems."""
    candidates: dict[str, dict[str, Any]] = {}

    for ent in active_problem_entities:
        if ent.get("label") != "PROBLEM" or not ent.get("is_active", False):
            continue
        icd10 = ent.get("icd10")
        link_score = ent.get("link_score")
        if not icd10 or link_score is None or float(link_score) < link_threshold:
            continue

        code = _normalize_icd10(str(icd10))
        span_len = int(ent["end_char"]) - int(ent["start_char"])
        section = ent.get("section")
        rank = (
            _section_priority(section),
            float(link_score),
            span_len,
        )
        existing = candidates.get(code)
        if existing is None or rank > existing["rank"]:
            section_label = section or "note"
            candidates[code] = {
                "icd10": code,
                "link_score": float(link_score),
                "evidence": f'{ent["text"]} ({section_label})',
                "rank": rank,
            }

    return candidates


def _hcc_set_from_codes(codes: list[str], age: int, sex: str) -> tuple[set[str], dict[str, str]]:
    if not codes:
        return set(), {}
    _, _, result = calculate_raf(codes, age, sex)
    labels = _hcc_label_map(result)
    return {str(h) for h in result.hcc_list}, labels


def _claimed_code_for_hcc(hcc: str, claimed_codes: list[str], age: int, sex: str) -> str:
    for code in claimed_codes:
        for mapping in map_icd10_to_hccs(code, age, sex):
            if mapping["hcc"] == hcc:
                return _normalize_icd10(code)
    return _normalize_icd10(claimed_codes[0]) if claimed_codes else ""


def _evidencing_code_for_hcc(
    hcc: str,
    evidenced: dict[str, dict[str, Any]],
    age: int,
    sex: str,
) -> tuple[str, str, float]:
    best: tuple[str, str, float] | None = None
    for code, payload in evidenced.items():
        for mapping in map_icd10_to_hccs(code, age, sex):
            if mapping["hcc"] != hcc:
                continue
            score = float(payload["link_score"])
            if best is None or score > best[2]:
                best = (code, payload["evidence"], score)
    if best:
        return best
    return "", "no supporting documentation found", 0.0


def detect_gaps(
    active_problem_entities: list[dict[str, Any]],
    claimed_codes: list[str],
    age: int,
    sex: str,
) -> dict[str, Any]:
    """Compare note-evidenced HCCs against claimed codes and compute RAF impact."""
    evidenced = _build_evidenced_codes(active_problem_entities)
    evidenced_codes = sorted(evidenced.keys())
    normalized_claimed = [_normalize_icd10(c) for c in claimed_codes if c and c.strip()]

    risk_current, _, current_result = calculate_raf(normalized_claimed, age, sex)
    combined_codes = sorted(set(normalized_claimed) | set(evidenced_codes))
    risk_potential, _, _ = calculate_raf(combined_codes, age, sex)
    risk_delta = round(risk_potential - risk_current, 4)

    evidenced_hccs, evidenced_labels = _hcc_set_from_codes(evidenced_codes, age, sex)
    claimed_hccs, claimed_labels = _hcc_set_from_codes(normalized_claimed, age, sex)
    all_labels = {**evidenced_labels, **claimed_labels, **_hcc_label_map(current_result)}

    gaps: list[dict[str, Any]] = []

    for hcc in sorted(evidenced_hccs - claimed_hccs):
        icd10, evidence, confidence = _evidencing_code_for_hcc(hcc, evidenced, age, sex)
        gaps.append(
            {
                "hcc": hcc,
                "label": all_labels.get(hcc, f"HCC {hcc}"),
                "status": "suspected",
                "icd10": icd10,
                "evidence": evidence,
                "confidence": confidence,
            }
        )

    for hcc in sorted(claimed_hccs - evidenced_hccs):
        gaps.append(
            {
                "hcc": hcc,
                "label": all_labels.get(hcc, f"HCC {hcc}"),
                "status": "unsupported",
                "icd10": _claimed_code_for_hcc(hcc, normalized_claimed, age, sex),
                "evidence": "no supporting documentation found",
                "confidence": 1.0,
            }
        )

    for hcc in sorted(evidenced_hccs & claimed_hccs):
        icd10, evidence, confidence = _evidencing_code_for_hcc(hcc, evidenced, age, sex)
        if not icd10:
            icd10 = _claimed_code_for_hcc(hcc, normalized_claimed, age, sex)
            evidence = evidence if evidence != "no supporting documentation found" else icd10
            confidence = 1.0
        gaps.append(
            {
                "hcc": hcc,
                "label": all_labels.get(hcc, f"HCC {hcc}"),
                "status": "confirmed",
                "icd10": icd10,
                "evidence": evidence,
                "confidence": confidence,
            }
        )

    return {
        "gaps": gaps,
        "risk_score_current": round(risk_current, 4),
        "risk_score_potential": round(risk_potential, 4),
        "risk_score_delta": risk_delta,
        "demographics": {"age": age, "sex": sex},
    }
