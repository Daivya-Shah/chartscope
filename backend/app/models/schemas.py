from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    note_text: str = Field(..., min_length=1, description="Clinical note text to analyze")
    claimed_codes: list[str] = Field(default_factory=list, description="ICD-10 codes already on the claim")


class Entity(BaseModel):
    text: str
    label: str
    start_char: int
    end_char: int
    section: str | None = None
    negated: bool = False
    historical: bool = False
    family: bool = False
    cui: str | None = None
    icd10: str | None = None
    score: float | None = None


class HccGap(BaseModel):
    hcc: str
    label: str
    status: str  # "gap" | "supported" | "unsupported"
    evidence: str
    icd10: str
    confidence: float


class AnalyzeResponse(BaseModel):
    deid_redactions: int
    entities: list[Entity]
    gaps: list[HccGap]
    risk_score: float
    fhir_bundle: dict


class ExampleNote(BaseModel):
    id: str
    title: str
    specialty: str
    note_text: str


class EvalResult(BaseModel):
    metric: str
    value: float
    description: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
