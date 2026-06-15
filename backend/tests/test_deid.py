"""Tests for PHI de-identification and clinical note ingestion."""

from app.pipeline.deid import deidentify
from app.pipeline.examples import EXAMPLE_NOTES
from app.pipeline.ingest import build_clinical_pipeline, clean_text, detect_sections


def test_deidentify_masks_name_date_and_mrn():
    text = (
        "Patient John Smith visited on January 15, 2020. "
        "Contact: john.smith@example.com, phone 555-123-4567. MRN SYN-10042."
    )
    result = deidentify(text)

    assert result["redaction_count"] >= 3
    assert "John Smith" not in result["clean_text"]
    assert "SYN-10042" not in result["clean_text"]
    assert "john.smith@example.com" not in result["clean_text"]
    assert any(span["type"] == "MRN" for span in result["phi_spans"])


def test_detect_sections_finds_clinical_headers():
    note = EXAMPLE_NOTES[0].note_text
    nlp = build_clinical_pipeline()
    doc = nlp(clean_text(note))
    sections = detect_sections(doc)

    names = " ".join(s["name"].upper() for s in sections)
    assert "ASSESSMENT" in names or "MEDICATIONS" in names


def test_clean_text_fixes_mtsamples_artifact():
    raw = "SUBJECTIVE:,  This 23-year-old white female presents with complaint of allergies."
    cleaned = clean_text(raw)
    assert ":,  " not in cleaned
    assert cleaned.startswith("SUBJECTIVE: This")
