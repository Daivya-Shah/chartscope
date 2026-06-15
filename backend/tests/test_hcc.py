"""Tests for CMS-HCC V28 gap detection."""

from app.pipeline.context import apply_context, filter_active_problems
from app.pipeline.deid import deidentify
from app.pipeline.examples import EXAMPLE_NOTES
from app.pipeline.hcc import demographics_from_text, detect_gaps
from app.pipeline.ingest import clean_text
from app.pipeline.linking import link_entities
from app.pipeline.ner import extract_entities

DIABETES_COMPLICATION_CODES = {"E11.22", "E11.42", "E11.21", "E11.29", "E11.40", "E11.41", "E11.43"}


def _analyze_gaps(note_text: str, claimed_codes: list[str]) -> dict:
    normalized = clean_text(note_text)
    deid = deidentify(normalized)
    text = deid["clean_text"]
    entities = link_entities(apply_context(text, extract_entities(text)))
    active = filter_active_problems(entities)
    demo = demographics_from_text(text)
    return detect_gaps(active, claimed_codes, age=int(demo["age"]), sex=str(demo["sex"]))


def test_demographics_from_diabetes_note():
    note = EXAMPLE_NOTES[0].note_text
    demo = demographics_from_text(clean_text(note))
    assert demo["age"] == 68
    assert demo["sex"] == "M"


def test_diabetes_example_suspected_complication_gap():
    note = EXAMPLE_NOTES[0]
    result = _analyze_gaps(note.note_text, note.claimed_codes)

    suspected = [g for g in result["gaps"] if g["status"] == "suspected"]
    assert suspected, "Expected at least one suspected HCC gap"

    complication_evidence = [
        g for g in suspected if g["icd10"] in DIABETES_COMPLICATION_CODES or "complication" in g["label"].lower()
    ]
    assert complication_evidence, (
        f"Expected suspected gap tied to diabetes complications, got: {suspected}"
    )

    assert result["risk_score_potential"] >= result["risk_score_current"]
    assert result["risk_score_delta"] >= 0


def test_unsupported_claimed_code_without_evidence():
    result = _analyze_gaps(
        "SYNTHETIC: 72-year-old female with essential hypertension. Assessment: hypertension at goal.",
        claimed_codes=["I10", "I50.22"],
    )
    unsupported = [g for g in result["gaps"] if g["status"] == "unsupported"]
    assert any(g["icd10"] == "I50.22" for g in unsupported)


def test_low_link_score_excluded_from_evidence():
    active_entities = [
        {
            "label": "PROBLEM",
            "text": "phantom condition",
            "is_active": True,
            "icd10": "I50.22",
            "link_score": 0.3,
            "section": "ASSESSMENT",
            "start_char": 0,
            "end_char": 10,
        }
    ]
    result = detect_gaps(active_entities, claimed_codes=["I10"], age=70, sex="M")
    suspected = [g for g in result["gaps"] if g["status"] == "suspected"]
    assert not any(g["icd10"] == "I50.22" for g in suspected)
