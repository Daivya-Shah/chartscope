"""Clinical NER via Hugging Face transformers (no scispaCy)."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_NER_MODEL = "d4data/biomedical-ner-all"

_ner_pipeline: Any | None = None
_label_map: dict[str, str] | None = None

# Raw entity-type names -> ChartScope schema labels.
_BASE_NORMALIZATION: dict[str, str] = {
    "Disease_disorder": "PROBLEM",
    "Sign_symptom": "PROBLEM",
    "Symptom": "PROBLEM",
    "Clinical_event": "PROBLEM",
    "Outcome": "PROBLEM",
    "Medication": "MEDICATION",
    "Drug": "MEDICATION",
    "Chemical": "MEDICATION",
    "Dosage": "MEDICATION",
    "Therapeutic_procedure": "PROCEDURE",
    "Surgery": "PROCEDURE",
    "Procedure": "PROCEDURE",
    "Diagnostic_procedure": "TEST",
    "Lab_value": "TEST",
    "Test": "TEST",
    "Biological_structure": "ANATOMY",
    "Anatomy": "ANATOMY",
    "Height": "VITAL",
    "Weight": "VITAL",
    "Blood_pressure": "VITAL",
    "Heart_rate": "VITAL",
    "Temperature": "VITAL",
    "Vital_sign": "VITAL",
}


def _raw_label_name(label: str) -> str:
    """Strip BIO prefix from a model label."""
    if label == "O":
        return "O"
    if "-" in label:
        return label.split("-", 1)[1]
    return label


def _build_label_map(id2label: dict[int | str, str]) -> dict[str, str]:
    raw_types: set[str] = set()
    for label in id2label.values():
        name = _raw_label_name(label)
        if name != "O":
            raw_types.add(name)

    label_map: dict[str, str] = {}
    unmapped: list[str] = []
    for raw in sorted(raw_types):
        normalized = _BASE_NORMALIZATION.get(raw)
        if normalized:
            label_map[raw] = normalized
        else:
            unmapped.append(raw)

    if unmapped:
        logger.warning("Unmapped biomedical NER labels (dropped): %s", ", ".join(unmapped))

    resolved = sorted(set(label_map.values()))
    logger.info(
        "ChartScope NER label map ready — raw types: %d, resolved schema labels: %s",
        len(label_map),
        resolved,
    )
    print(f"[ner] Resolved label set: {resolved}")
    return label_map


def _get_ner_pipeline() -> tuple[Any, dict[str, str]]:
    global _ner_pipeline, _label_map

    if _ner_pipeline is not None and _label_map is not None:
        return _ner_pipeline, _label_map

    from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

    model_id = os.getenv("CHARTSCOPE_NER_MODEL", DEFAULT_NER_MODEL)
    logger.info("Loading HuggingFace NER model: %s", model_id)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForTokenClassification.from_pretrained(model_id)
    _label_map = _build_label_map(model.config.id2label)

    _ner_pipeline = pipeline(
        "token-classification",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="first",
        device=-1,
    )
    return _ner_pipeline, _label_map


def _normalize_label(raw_group: str, label_map: dict[str, str]) -> str | None:
    name = _raw_label_name(raw_group)
    return label_map.get(name)


def _merge_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe overlaps — prefer longer span, then higher score."""
    ranked = sorted(
        entities,
        key=lambda e: (
            -(e["end_char"] - e["start_char"]),
            -e["score"],
            e["start_char"],
        ),
    )
    kept: list[dict[str, Any]] = []
    occupied: list[tuple[int, int]] = []

    for ent in ranked:
        start, end = ent["start_char"], ent["end_char"]
        if any(not (end <= o_start or start >= o_end) for o_start, o_end in occupied):
            continue
        kept.append(ent)
        occupied.append((start, end))

    return sorted(kept, key=lambda e: e["start_char"])


def extract_entities(text: str) -> list[dict[str, Any]]:
    """Run HF token-classification NER and return normalized ChartScope entities."""
    if not text or not text.strip():
        return []

    ner_pipe, label_map = _get_ner_pipeline()
    predictions = ner_pipe(text)

    entities: list[dict[str, Any]] = []
    for pred in predictions:
        raw_group = pred.get("entity_group") or pred.get("entity") or ""
        normalized = _normalize_label(raw_group, label_map)
        if not normalized:
            continue

        start = int(pred["start"])
        end = int(pred["end"])
        entities.append(
            {
                "text": text[start:end],
                "label": normalized,
                "start_char": start,
                "end_char": end,
                "score": float(pred["score"]),
            }
        )

    return _merge_entities(entities)
