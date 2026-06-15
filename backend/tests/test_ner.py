"""Tests for HuggingFace NER and medspaCy ConText assertion layer."""

from app.pipeline.context import apply_context, filter_active_problems
from app.pipeline.deid import deidentify
from app.pipeline.examples import EXAMPLE_NOTES
from app.pipeline.ingest import clean_text
from app.pipeline.ner import extract_entities


def _problem_texts(entities: list[dict]) -> list[str]:
    return [e["text"].lower() for e in entities if e["label"] == "PROBLEM"]


def test_extract_entities_diabetes_example_problems():
    note = clean_text(EXAMPLE_NOTES[0].note_text)
    deid = deidentify(note)
    entities = extract_entities(deid["clean_text"])
    problems = _problem_texts(entities)

    assert any("kidney" in t or "ckd" in t for t in problems), problems
    assert any("polyneuropathy" in t or "neuropathy" in t for t in problems), problems


def test_context_negated_symptoms_excluded():
    text = (
        "REVIEW OF SYSTEMS: No chest pain or dyspnea. "
        "Patient otherwise well."
    )
    entities = extract_entities(text)
    annotated = apply_context(text, entities)
    active = filter_active_problems(annotated)

    negated = [e for e in annotated if e.get("negated")]
    assert negated, "Expected at least one negated entity"
    assert not any("chest pain" in e["text"].lower() for e in active)
    assert not any("dyspnea" in e["text"].lower() for e in active)


def test_context_historical_problem_excluded():
    text = "Patient has history of myocardial infarction in 2015. Active hypertension."
    entities = extract_entities(text)
    annotated = apply_context(text, entities)
    active = filter_active_problems(annotated)

    historical = [e for e in annotated if e.get("historical")]
    assert historical, "Expected at least one historical entity"
    assert not any("infarction" in e["text"].lower() for e in active)


def test_daily_not_masked_as_date():
    result = deidentify("Take lisinopril 20 mg daily for hypertension.")
    assert "daily" in result["clean_text"]
    assert "[DATE]" not in result["clean_text"]
