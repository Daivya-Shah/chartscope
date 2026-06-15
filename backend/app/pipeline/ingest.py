"""Clinical note ingestion: text cleaning, section detection, sentence splitting."""

from __future__ import annotations

import re
from typing import Any

import medspacy
from spacy.language import Language

_clinical_nlp: Language | None = None

# MTSamples export often inserts ",  " after section headers (e.g. "SUBJECTIVE:,  This...")
_MTSAMPLES_HEADER_ARTIFACT = re.compile(r":,\s+")
_MULTI_SPACE = re.compile(r"[^\S\n]+")
_EXCESS_NEWLINES = re.compile(r"\n{3,}")


def clean_text(raw: str) -> str:
    """Normalize whitespace and fix common MTSamples transcription artifacts."""
    if not raw:
        return ""

    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = _MTSAMPLES_HEADER_ARTIFACT.sub(": ", text)
    # Residual double-comma spacing after headers: ",  word" -> ", word"
    text = re.sub(r",\s{2,}(?=[A-Za-z])", ", ", text)
    text = _EXCESS_NEWLINES.sub("\n\n", text)
    lines = [_MULTI_SPACE.sub(" ", line).strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)
    return text.strip()


def build_clinical_pipeline() -> Language:
    """Return cached spaCy pipeline with medspaCy Sectionizer + ConText."""
    global _clinical_nlp
    if _clinical_nlp is not None:
        return _clinical_nlp

    # Parser disabled — PyRuSH sentence boundaries conflict with dependency parse.
    _clinical_nlp = medspacy.load(
        "en_core_web_sm",
        disable=["parser"],
        medspacy_enable={
            "medspacy_pyrush",
            "medspacy_sectionizer",
            "medspacy_context",
        },
    )
    return _clinical_nlp


def detect_sections(doc) -> list[dict[str, Any]]:
    """Extract clinical sections from a processed spaCy Doc."""
    sections: list[dict[str, Any]] = []

    for section in doc._.sections:
        title_start, title_end = section.title_span
        body_start, body_end = section.body_span

        if title_end > title_start:
            name = doc[title_start:title_end].text.strip().rstrip(":")
        else:
            name = (section.category or "UNKNOWN").strip()

        if body_end > body_start:
            span_start = doc[body_start].idx
            span_end = doc[body_end - 1].idx + len(doc[body_end - 1])
        elif title_end > title_start:
            span_start = doc[title_start].idx
            span_end = doc[title_end - 1].idx + len(doc[title_end - 1])
        else:
            continue

        text = doc.text[span_start:span_end].strip()
        if not text:
            continue

        sections.append(
            {
                "name": name,
                "start_char": span_start,
                "end_char": span_end,
                "text": text,
            }
        )

    return sections


def sentence_split(text: str) -> list[str]:
    """Split cleaned note text into sentences."""
    nlp = build_clinical_pipeline()
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def ingest_note(note_text: str) -> dict[str, Any]:
    """Clean text and detect sections (de-id handled separately upstream)."""
    cleaned = clean_text(note_text)
    nlp = build_clinical_pipeline()
    doc = nlp(cleaned)
    return {
        "text": cleaned,
        "sections": detect_sections(doc),
        "sentences": sentence_split(cleaned),
    }
