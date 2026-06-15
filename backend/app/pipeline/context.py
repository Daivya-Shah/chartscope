"""Assertion detection (negation, temporality, experiencer) via medspaCy ConText."""

from __future__ import annotations

import re
from typing import Any

from spacy.util import filter_spans

from app.pipeline.ingest import build_clinical_pipeline, detect_sections

_NEGATION_CLAUSE = re.compile(
    r"\b(no|denies|denied|without|negative for|absence of)\b",
    re.IGNORECASE,
)
_HISTORY_CLAUSE = re.compile(
    r"\b(history of|past history of|h/o|remote history of)\b",
    re.IGNORECASE,
)
_FAMILY_CLAUSE = re.compile(
    r"\b(family history of|fh:|f/h of|mother with|father with)\b",
    re.IGNORECASE,
)


def _clause_before(text: str, start: int) -> str:
    """Return clause text preceding a character offset (since last period/newline)."""
    boundary = max(text.rfind(".", 0, start), text.rfind("\n", 0, start))
    return text[boundary + 1 : start]


def _heuristic_negated(text: str, start: int) -> bool:
    return bool(_NEGATION_CLAUSE.search(_clause_before(text, start)))


def _heuristic_historical(text: str, start: int) -> bool:
    return bool(_HISTORY_CLAUSE.search(_clause_before(text, start)))


def _heuristic_family(text: str, start: int) -> bool:
    return bool(_FAMILY_CLAUSE.search(_clause_before(text, start)))


def _section_for_entity(start: int, end: int, sections: list[dict[str, Any]]) -> str | None:
    best: str | None = None
    best_overlap = 0
    for section in sections:
        sec_start = section["start_char"]
        sec_end = section["end_char"]
        overlap = max(0, min(end, sec_end) - max(start, sec_start))
        if overlap > best_overlap:
            best_overlap = overlap
            best = section["name"]
    return best


def _annotate_active(ent: dict[str, Any]) -> None:
    if ent["label"] != "PROBLEM":
        ent["is_active"] = True
        ent["drop_reason"] = None
        return

    if ent.get("negated"):
        ent["is_active"] = False
        ent["drop_reason"] = "negated"
    elif ent.get("historical"):
        ent["is_active"] = False
        ent["drop_reason"] = "historical"
    elif ent.get("family"):
        ent["is_active"] = False
        ent["drop_reason"] = "family history"
    elif ent.get("uncertain"):
        ent["is_active"] = False
        ent["drop_reason"] = "uncertain"
    else:
        ent["is_active"] = True
        ent["drop_reason"] = None


def filter_active_problems(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return PROBLEM entities that are active (not negated/historical/family/uncertain)."""
    return [
        ent
        for ent in entities
        if ent.get("label") == "PROBLEM" and ent.get("is_active", False)
    ]


def _find_context_span(doc, start: int, end: int):
    for span in doc.ents:
        if span.start_char == start and span.end_char == end:
            return span
        if span.start_char <= start and span.end_char >= end:
            return span
    return None


def apply_context(
    text: str,
    entities: list[dict[str, Any]],
    sections: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Attach medspaCy ConText assertion flags and clinical section to HF entities."""
    if not entities:
        return []

    nlp = build_clinical_pipeline()
    with nlp.select_pipes(disable=["medspacy_context"]):
        doc = nlp(text)

    if sections is None:
        sections = detect_sections(doc)

    spans = []
    span_keys: list[tuple[int, int]] = []
    for ent in entities:
        span = doc.char_span(
            ent["start_char"],
            ent["end_char"],
            label=ent["label"],
            alignment_mode="expand",
        )
        if span is None:
            continue
        spans.append(span)
        span_keys.append((ent["start_char"], ent["end_char"]))

    doc.ents = filter_spans(spans)
    doc = nlp.get_pipe("medspacy_context")(doc)

    enriched: list[dict[str, Any]] = []
    for ent in entities:
        updated = dict(ent)
        span = _find_context_span(doc, ent["start_char"], ent["end_char"])

        updated["negated"] = (
            bool(getattr(span._, "is_negated", False)) if span is not None else False
        ) or _heuristic_negated(text, ent["start_char"])
        updated["uncertain"] = (
            bool(getattr(span._, "is_uncertain", False)) if span is not None else False
        )
        updated["historical"] = (
            bool(getattr(span._, "is_historical", False)) if span is not None else False
        ) or _heuristic_historical(text, ent["start_char"])
        updated["family"] = (
            bool(getattr(span._, "is_family", False)) if span is not None else False
        ) or _heuristic_family(text, ent["start_char"])

        updated["section"] = _section_for_entity(
            updated["start_char"],
            updated["end_char"],
            sections,
        )
        _annotate_active(updated)
        enriched.append(updated)

    return enriched
