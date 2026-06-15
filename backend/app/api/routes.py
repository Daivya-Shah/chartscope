from fastapi import APIRouter

from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    Entity,
    EvalResult,
    ExampleNote,
    HccGap,
)

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


# TODO (build step: examples): serve curated example notes from MTSamples/Synthea
@router.get("/examples", response_model=list[ExampleNote])
async def get_examples() -> list[ExampleNote]:
    return [
        ExampleNote(
            id="ex-001",
            title="Diabetes Follow-up",
            specialty="Internal Medicine",
            note_text=(
                "ASSESSMENT: 58-year-old male with type 2 diabetes mellitus, "
                "well controlled on metformin 1000mg BID. HbA1c 7.1%. "
                "No chest pain or shortness of breath."
            ),
        ),
        ExampleNote(
            id="ex-002",
            title="CHF Exacerbation",
            specialty="Cardiology",
            note_text=(
                "HISTORY: Patient presents with worsening dyspnea and lower extremity edema. "
                "Known history of congestive heart failure, EF 35%. "
                "PLAN: Increase furosemide, daily weights."
            ),
        ),
    ]


# TODO (build step: mtsamples): load random row from data/raw/mtsamples.csv
@router.get("/mtsamples/random", response_model=ExampleNote)
async def get_random_mtsample() -> ExampleNote:
    return ExampleNote(
        id="mts-0042",
        title="Orthopedic Consultation",
        specialty="Orthopedic",
        note_text=(
            "CHIEF COMPLAINT: Right knee pain.\n\n"
            "HISTORY: 45-year-old female with 3-week history of progressive right knee pain, "
            "worse with stair climbing. No trauma. Past medical history significant for obesity.\n\n"
            "EXAM: Mild effusion, tenderness over medial joint line. Full ROM with discomfort.\n\n"
            "IMPRESSION: Medial meniscus tear, right knee.\n\n"
            "PLAN: MRI knee, physical therapy, NSAIDs PRN."
        ),
    )


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
