from fastapi import APIRouter, HTTPException, Query

from app.data.loaders import get_random_note, list_specialties
from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    Entity,
    EvalResult,
    ExampleNote,
    HccGap,
    RandomNote,
    SpecialtyCount,
)
from app.pipeline.examples import EXAMPLE_NOTES

router = APIRouter()


# ---------------------------------------------------------------------------
# TODO (build step: analyze pipeline): wire ingest → deid → ner → context
#       → linking → hcc → fhir_export and return real results
# ---------------------------------------------------------------------------
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_note(request: AnalyzeRequest) -> AnalyzeResponse:
    return AnalyzeResponse(
        deid_redactions=2,
        entities=[
            Entity(
                text="type 2 diabetes mellitus",
                label="CONDITION",
                start_char=45,
                end_char=69,
                section="Assessment",
                negated=False,
                historical=False,
                family=False,
                cui="C0011860",
                icd10="E11.9",
                score=0.94,
            ),
            Entity(
                text="metformin",
                label="MEDICATION",
                start_char=120,
                end_char=129,
                section="Medications",
                negated=False,
                score=0.91,
            ),
            Entity(
                text="no chest pain",
                label="SYMPTOM",
                start_char=200,
                end_char=213,
                section="Review of Systems",
                negated=True,
                score=0.88,
            ),
        ],
        gaps=[
            HccGap(
                hcc="HCC19",
                label="Diabetes without Complication",
                status="supported",
                evidence="type 2 diabetes mellitus documented in Assessment",
                icd10="E11.9",
                confidence=0.92,
            ),
            HccGap(
                hcc="HCC85",
                label="Congestive Heart Failure",
                status="gap",
                evidence="No CHF documentation found; consider if clinically present",
                icd10="I50.9",
                confidence=0.71,
            ),
        ],
        risk_score=1.234,
        fhir_bundle={
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Condition",
                        "code": {
                            "coding": [
                                {
                                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                                    "code": "E11.9",
                                    "display": "Type 2 diabetes mellitus without complications",
                                }
                            ]
                        },
                        "clinicalStatus": {
                            "coding": [
                                {"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}
                            ]
                        },
                    }
                }
            ],
        },
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
