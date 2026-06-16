"""Tests for FHIR R4 Bundle export."""

import json

from app.pipeline.context import apply_context, filter_active_problems
from app.pipeline.deid import deidentify
from app.pipeline.examples import EXAMPLE_NOTES
from app.pipeline.fhir_export import to_fhir_bundle
from app.pipeline.hcc import demographics_from_text, detect_gaps
from app.pipeline.ingest import clean_text
from app.pipeline.linking import link_entities
from app.pipeline.ner import extract_entities


def _diabetes_analysis() -> dict:
    note = EXAMPLE_NOTES[0]
    text = deidentify(clean_text(note.note_text))["clean_text"]
    entities = link_entities(apply_context(text, extract_entities(text)))
    active = filter_active_problems(entities)
    demo = demographics_from_text(text)
    gaps = detect_gaps(active, note.claimed_codes, int(demo["age"]), str(demo["sex"]))
    meds = [e for e in entities if e.get("label") == "MEDICATION" and e.get("rxnorm")]
    bundle, valid, errors = to_fhir_bundle(
        demographics=gaps["demographics"],
        active_problems=[e for e in active if e.get("icd10")],
        medications=meds,
        gaps=gaps["gaps"],
        risk={
            "risk_score_current": gaps["risk_score_current"],
            "risk_score_potential": gaps["risk_score_potential"],
            "risk_score_delta": gaps["risk_score_delta"],
        },
    )
    return {"bundle": bundle, "valid": valid, "errors": errors}


def _resources_by_type(bundle: dict, resource_type: str) -> list[dict]:
    return [
        entry["resource"]
        for entry in bundle.get("entry", [])
        if entry.get("resource", {}).get("resourceType") == resource_type
    ]


def test_diabetes_bundle_validates_and_contains_core_resources():
    result = _diabetes_analysis()
    assert result["valid"] is True, result["errors"]
    assert not result["errors"]

    bundle = result["bundle"]
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"

    patients = _resources_by_type(bundle, "Patient")
    assert patients, "Expected Patient resource"
    assert patients[0]["gender"] in {"male", "female", "unknown"}

    conditions = _resources_by_type(bundle, "Condition")
    assert conditions, "Expected at least one Condition"
    icd_codes = [
        coding["code"]
        for cond in conditions
        for coding in cond.get("code", {}).get("coding", [])
        if coding.get("system") == "http://hl7.org/fhir/sid/icd-10-cm"
    ]
    assert any(code.startswith("E11") for code in icd_codes), icd_codes

    risks = _resources_by_type(bundle, "RiskAssessment")
    assert risks, "Expected RiskAssessment"
    predictions = risks[0].get("prediction") or []
    assert any("HCC 37" in (p.get("outcome", {}).get("text") or "") for p in predictions)


def test_diabetes_bundle_round_trips_through_fhir_resources():
    bundle = _diabetes_analysis()["bundle"]
    try:
        from fhir.resources.R4B.bundle import Bundle
    except ImportError:
        from fhir.resources.bundle import Bundle

    parsed = Bundle.model_validate_json(json.dumps(bundle))
    reparsed = Bundle.model_validate_json(parsed.json())
    assert reparsed.type == "collection"
    assert len(reparsed.entry or []) >= 3
