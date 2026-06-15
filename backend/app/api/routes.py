from fastapi import APIRouter, HTTPException, Query

from app.data.loaders import get_random_note, list_specialties
from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    Entity,
    EvalResult,
    ExampleNote,
    PhiSpan,
    RandomNote,
    Section,
    SpecialtyCount,
)
from app.pipeline.context import apply_context
from app.pipeline.deid import deidentify
from app.pipeline.examples import EXAMPLE_NOTES
from app.pipeline.ingest import build_clinical_pipeline, clean_text, detect_sections
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

    # TODO (step 5): HCC gap detection vs request.claimed_codes using filter_active_problems
    # TODO (step 6): FHIR Bundle export from entities + gaps

    return AnalyzeResponse(
        deid_redactions=deid_result["redaction_count"],
        deid_text=normalized,
        phi_spans=[PhiSpan(type=s["type"], start=s["start"], end=s["end"]) for s in deid_result["phi_spans"]],
        sections=[
            Section(name=s["name"], start_char=s["start_char"], end_char=s["end_char"])
            for s in sections_raw
        ],
        entities=[Entity(**ent) for ent in annotated_entities],
        gaps=[],
        risk_score=0.0,
        fhir_bundle={},
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


# TODO (build step: eval): run eval_harness.py metrics against gold-standard fixtures
@router.get("/eval", response_model=list[EvalResult])
async def get_eval_results() -> list[EvalResult]:
    return [
        EvalResult(
            metric="ner_f1",
            value=0.0,
            description="Named entity recognition F1 (stub — pipeline not yet implemented)",
        ),
        EvalResult(
            metric="hcc_gap_precision",
            value=0.0,
            description="HCC gap detection precision (stub)",
        ),
        EvalResult(
            metric="deid_recall",
            value=0.0,
            description="PHI redaction recall (stub)",
        ),
    ]
