from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.data.loaders import get_random_note, list_specialties
from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    Entity,
    ExampleNote,
    KeyProblem,
    PatientDemographics,
    PhiSpan,
    RandomNote,
    Section,
    SpecialtyCount,
)
from app.pipeline.context import apply_context, filter_active_problems
from app.pipeline.deid import deidentify
from app.pipeline.examples import EXAMPLE_NOTES
from app.pipeline.fhir_export import to_fhir_bundle
from app.pipeline.hcc import demographics_from_text, detect_gaps
from app.pipeline.ingest import build_clinical_pipeline, clean_text, detect_sections
from app.pipeline.linking import link_entities
from app.pipeline.ner import extract_entities

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_note(request: AnalyzeRequest) -> AnalyzeResponse:
    # De-identification runs FIRST by design — PHI must be masked before downstream NLP.
    deid_result = deidentify(request.note_text)
    normalized = clean_text(deid_result["clean_text"])

    nlp = build_clinical_pipeline()
    doc = nlp(normalized)
    sections_raw = detect_sections(doc)

    raw_entities = extract_entities(normalized)
    annotated_entities = apply_context(normalized, raw_entities, sections=sections_raw)
    linked_entities = link_entities(annotated_entities)

    demo = demographics_from_text(normalized)
    active_problems = filter_active_problems(linked_entities)
    gap_result = detect_gaps(
        active_problems,
        request.claimed_codes,
        age=int(demo["age"]),
        sex=str(demo["sex"]),
    )

    medications = [e for e in linked_entities if e.get("label") == "MEDICATION" and e.get("rxnorm")]
    vitals = [e for e in linked_entities if e.get("label") == "VITAL"]
    fhir_bundle, fhir_valid, fhir_errors = to_fhir_bundle(
        demographics=gap_result["demographics"],
        key_problems=gap_result["key_problems"],
        medications=medications,
        gaps=gap_result["gaps"],
        risk={
            "risk_score_current": gap_result["risk_score_current"],
            "risk_score_potential": gap_result["risk_score_potential"],
            "risk_score_delta": gap_result["risk_score_delta"],
        },
        vitals=vitals,
    )

    return AnalyzeResponse(
        deid_redactions=deid_result["redaction_count"],
        deid_text=normalized,
        phi_spans=[PhiSpan(type=s["type"], start=s["start"], end=s["end"]) for s in deid_result["phi_spans"]],
        sections=[
            Section(name=s["name"], start_char=s["start_char"], end_char=s["end_char"])
            for s in sections_raw
        ],
        entities=[Entity(**ent) for ent in linked_entities],
        key_problems=[KeyProblem(**item) for item in gap_result["key_problems"]],
        gaps=gap_result["gaps"],
        risk_score=gap_result["risk_score_current"],
        risk_score_current=gap_result["risk_score_current"],
        risk_score_potential=gap_result["risk_score_potential"],
        risk_score_delta=gap_result["risk_score_delta"],
        demographics=PatientDemographics(**gap_result["demographics"]),
        fhir_bundle=fhir_bundle,
        fhir_valid=fhir_valid,
        fhir_errors=fhir_errors,
    )


@router.get("/examples", response_model=list[ExampleNote])
async def get_examples() -> list[ExampleNote]:
    return EXAMPLE_NOTES


@router.get("/mtsamples/random", response_model=RandomNote)
async def get_random_mtsample(
    specialty: str | None = Query(default=None, description="Filter by medical specialty"),
) -> RandomNote:
    try:
        note = get_random_note(specialty=specialty)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RandomNote(**note)


@router.get("/mtsamples/specialties", response_model=list[SpecialtyCount])
async def get_mtsample_specialties() -> list[SpecialtyCount]:
    rows = list_specialties()
    return [SpecialtyCount(**row) for row in rows]


# Fine-tune / baseline metrics for the Evaluation tab.
@router.get("/eval")
async def get_eval_metrics() -> dict:
    metrics_path = Path(__file__).resolve().parents[2] / "eval" / "finetune_metrics.json"
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="finetune_metrics.json not found")
    return json.loads(metrics_path.read_text(encoding="utf-8"))
