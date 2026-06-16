"""Tests for CMS-HCC V28 gap detection."""

from app.pipeline.context import apply_context, filter_active_problems
from app.pipeline.deid import deidentify
from app.pipeline.examples import EXAMPLE_NOTES
from app.pipeline.hcc import demographics_from_text, detect_gaps, select_key_problems
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


def test_diabetes_example_suspected_and_superseded():
    note = EXAMPLE_NOTES[0]
    result = _analyze_gaps(note.note_text, note.claimed_codes)

    suspected = [g for g in result["gaps"] if g["status"] == "suspected"]
    assert any(g["hcc"] == "37" for g in suspected), suspected
    assert any(g.get("recommendation") for g in suspected)

    superseded = [g for g in result["gaps"] if g["status"] == "superseded"]
    assert any(g["icd10"] == "E11.9" and g["hcc"] == "38" for g in superseded), superseded
    assert all(g["status"] != "unsupported" or g["icd10"] != "E11.9" for g in result["gaps"])

    complication_evidence = [
        g
        for g in suspected
        if g["icd10"] in DIABETES_COMPLICATION_CODES or "complication" in g["label"].lower()
    ]
    assert complication_evidence, f"Expected suspected gap tied to diabetes complications, got: {suspected}"

    assert result["risk_score_potential"] >= result["risk_score_current"]
    assert abs(result["risk_score_delta"]) < 0.01


def test_chf_example_positive_risk_delta():
    note = EXAMPLE_NOTES[1]
    result = _analyze_gaps(note.note_text, note.claimed_codes)

    suspected = [g for g in result["gaps"] if g["status"] == "suspected"]
    assert suspected, "Expected suspected heart failure HCC gap"
    assert any("heart failure" in g["label"].lower() for g in suspected)
    assert result["risk_score_delta"] > 0


def test_copd_example_confirmed_hcc():
    note = EXAMPLE_NOTES[2]
    result = _analyze_gaps(note.note_text, note.claimed_codes)

    confirmed = [g for g in result["gaps"] if g["status"] == "confirmed"]
    assert any(g["hcc"] == "280" for g in confirmed), confirmed


def test_unsupported_claimed_code_without_evidence():
    result = _analyze_gaps(
        "SYNTHETIC: 72-year-old female with essential hypertension. Assessment: hypertension at goal.",
        claimed_codes=["I10", "I50.22"],
    )
    unsupported = [g for g in result["gaps"] if g["status"] == "unsupported"]
    assert any(g["icd10"] == "I50.22" for g in unsupported)
    assert all(g.get("recommendation") for g in unsupported)


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


def test_select_key_problems_dedupes_and_drops_vague_r_symptoms():
    active = [
        {
            "label": "PROBLEM",
            "text": "numbness",
            "is_active": True,
            "icd10": "R53.1",
            "icd10_desc": "Weakness",
            "link_score": 0.72,
            "section": "HPI",
            "start_char": 0,
            "end_char": 8,
        },
        {
            "label": "PROBLEM",
            "text": "type 2 diabetes with chronic kidney disease",
            "is_active": True,
            "icd10": "E11.22",
            "icd10_desc": "Type 2 diabetes mellitus with diabetic chronic kidney disease",
            "link_score": 0.91,
            "section": "ASSESSMENT",
            "start_char": 10,
            "end_char": 53,
        },
        {
            "label": "PROBLEM",
            "text": "diabetes with CKD",
            "is_active": True,
            "icd10": "E11.22",
            "icd10_desc": "Type 2 diabetes mellitus with diabetic chronic kidney disease",
            "link_score": 0.88,
            "section": "PLAN",
            "start_char": 60,
            "end_char": 77,
        },
    ]
    selected = select_key_problems(active)
    codes = [item["icd10"] for item in selected]
    assert codes == ["E11.22"]
    assert "R53.1" not in codes
    assert selected[0]["section"] == "ASSESSMENT"
