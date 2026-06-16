"""FHIR R4 Bundle export — US Core / Da Vinci-aligned upcycling."""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

US_CORE_PATIENT = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
US_CORE_CONDITION_ENCOUNTER = (
    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition-encounter-diagnosis"
)
DAVINCI_RISK_ASSESSMENT = (
    "http://hl7.org/fhir/us/davinci-ra/StructureDefinition/drc-riskAssessment"
)

ICD10_SYSTEM = "http://hl7.org/fhir/sid/icd-10-cm"
RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SNOMED_SYSTEM = "http://snomed.info/sct"
CONDITION_CLINICAL = "http://terminology.hl7.org/CodeSystem/condition-clinical"
CONDITION_VERIFICATION = "http://terminology.hl7.org/CodeSystem/condition-ver-status"
CONDITION_CATEGORY = "http://terminology.hl7.org/CodeSystem/condition-category"
OBSERVATION_CATEGORY = "http://terminology.hl7.org/CodeSystem/observation-category"

SYNTHETIC_PATIENT_ID = "chartscope-synthetic-patient"


def _load_fhir_models() -> dict[str, Any]:
    """Import R4B models when available, else default R4-compatible classes."""
    try:
        from fhir.resources.R4B.annotation import Annotation
        from fhir.resources.R4B.bundle import Bundle, BundleEntry
        from fhir.resources.R4B.codeableconcept import CodeableConcept
        from fhir.resources.R4B.coding import Coding
        from fhir.resources.R4B.condition import Condition
        from fhir.resources.R4B.identifier import Identifier
        from fhir.resources.R4B.medicationstatement import MedicationStatement
        from fhir.resources.R4B.meta import Meta
        from fhir.resources.R4B.observation import Observation
        from fhir.resources.R4B.patient import Patient
        from fhir.resources.R4B.reference import Reference
        from fhir.resources.R4B.riskassessment import RiskAssessment, RiskAssessmentPrediction

        return {
            "Annotation": Annotation,
            "Bundle": Bundle,
            "BundleEntry": BundleEntry,
            "CodeableConcept": CodeableConcept,
            "Coding": Coding,
            "Condition": Condition,
            "Identifier": Identifier,
            "MedicationStatement": MedicationStatement,
            "Meta": Meta,
            "Observation": Observation,
            "Patient": Patient,
            "Reference": Reference,
            "RiskAssessment": RiskAssessment,
            "RiskAssessmentPrediction": RiskAssessmentPrediction,
        }
    except ImportError:
        from fhir.resources.annotation import Annotation
        from fhir.resources.bundle import Bundle, BundleEntry
        from fhir.resources.codeableconcept import CodeableConcept
        from fhir.resources.coding import Coding
        from fhir.resources.condition import Condition
        from fhir.resources.identifier import Identifier
        from fhir.resources.medicationstatement import MedicationStatement
        from fhir.resources.meta import Meta
        from fhir.resources.observation import Observation
        from fhir.resources.patient import Patient
        from fhir.resources.reference import Reference
        from fhir.resources.riskassessment import RiskAssessment, RiskAssessmentPrediction

        return {
            "Annotation": Annotation,
            "Bundle": Bundle,
            "BundleEntry": BundleEntry,
            "CodeableConcept": CodeableConcept,
            "Coding": Coding,
            "Condition": Condition,
            "Identifier": Identifier,
            "MedicationStatement": MedicationStatement,
            "Meta": Meta,
            "Observation": Observation,
            "Patient": Patient,
            "Reference": Reference,
            "RiskAssessment": RiskAssessment,
            "RiskAssessmentPrediction": RiskAssessmentPrediction,
        }


def _gender_from_demographics(sex: str) -> str:
    token = (sex or "M").upper()
    if token in {"F", "FEMALE"}:
        return "female"
    if token in {"M", "MALE"}:
        return "male"
    return "unknown"


def _approx_birth_date(age: int) -> str:
    year = date.today().year - max(0, min(age, 120))
    return f"{year}-01-01"


def _patient_reference(models: dict[str, Any]) -> Any:
    return models["Reference"](reference=f"Patient/{SYNTHETIC_PATIENT_ID}")


def _build_patient(demo: dict[str, Any], models: dict[str, Any]) -> Any:
    Patient = models["Patient"]
    Meta = models["Meta"]
    Identifier = models["Identifier"]

    age = int(demo.get("age", 70))
    sex = str(demo.get("sex", "M"))

    return Patient(
        id=SYNTHETIC_PATIENT_ID,
        meta=Meta(profile=[US_CORE_PATIENT]),
        identifier=[
            Identifier(
                system="urn:chartscope:synthetic",
                value=f"synthetic-{age}-{sex.lower()}",
            )
        ],
        gender=_gender_from_demographics(sex),
        birthDate=_approx_birth_date(age),
    )


def _condition_evidence(entity: dict[str, Any]) -> str:
    section = entity.get("section") or "note"
    return f'{entity.get("text", "").strip()} ({section})'


def _build_condition(entity: dict[str, Any], models: dict[str, Any], index: int) -> Any:
    Condition = models["Condition"]
    Meta = models["Meta"]
    CodeableConcept = models["CodeableConcept"]
    Coding = models["Coding"]
    Annotation = models["Annotation"]

    icd10 = str(entity["icd10"])
    codings = [
        Coding(
            system=ICD10_SYSTEM,
            code=icd10,
            display=entity.get("icd10_desc") or icd10,
        )
    ]
    if entity.get("cui"):
        codings.append(Coding(system=SNOMED_SYSTEM, code=str(entity["cui"])))

    return Condition(
        id=f"condition-{index}",
        meta=Meta(profile=[US_CORE_CONDITION_ENCOUNTER]),
        clinicalStatus=CodeableConcept(
            coding=[Coding(system=CONDITION_CLINICAL, code="active")]
        ),
        verificationStatus=CodeableConcept(
            coding=[Coding(system=CONDITION_VERIFICATION, code="confirmed")]
        ),
        category=[
            CodeableConcept(
                coding=[Coding(system=CONDITION_CATEGORY, code="encounter-diagnosis")]
            )
        ],
        code=CodeableConcept(coding=codings),
        subject=_patient_reference(models),
        note=[Annotation(text=_condition_evidence(entity))],
    )


def _build_medication(entity: dict[str, Any], models: dict[str, Any], index: int) -> Any:
    MedicationStatement = models["MedicationStatement"]
    CodeableConcept = models["CodeableConcept"]
    Coding = models["Coding"]

    return MedicationStatement(
        id=f"medication-{index}",
        status="active",
        medicationCodeableConcept=CodeableConcept(
            coding=[
                Coding(
                    system=RXNORM_SYSTEM,
                    code=str(entity["rxnorm"]),
                    display=entity.get("rxnorm_name") or entity.get("text"),
                )
            ]
        ),
        subject=_patient_reference(models),
    )


def _build_observation(entity: dict[str, Any], models: dict[str, Any], index: int) -> Any:
    Observation = models["Observation"]
    CodeableConcept = models["CodeableConcept"]
    Coding = models["Coding"]

    label = entity.get("label") or "VITAL"
    text = entity.get("text", label)

    return Observation(
        id=f"observation-{index}",
        status="final",
        category=[
            CodeableConcept(
                coding=[Coding(system=OBSERVATION_CATEGORY, code="vital-signs")]
            )
        ],
        code=CodeableConcept(text=text),
        subject=_patient_reference(models),
        valueString=text,
    )


def _build_risk_assessment(
    gaps: list[dict[str, Any]],
    risk: dict[str, Any],
    models: dict[str, Any],
) -> Any | None:
    relevant = [g for g in gaps if g.get("status") in {"suspected", "confirmed"}]
    if not relevant and not risk:
        return None

    RiskAssessment = models["RiskAssessment"]
    RiskAssessmentPrediction = models["RiskAssessmentPrediction"]
    Meta = models["Meta"]
    CodeableConcept = models["CodeableConcept"]
    Annotation = models["Annotation"]

    predictions = [
        RiskAssessmentPrediction(
            outcome=CodeableConcept(
                text=f'HCC {g["hcc"]}: {g.get("label", "")}'.strip()
            ),
            rationale=g.get("recommendation") or g.get("evidence"),
        )
        for g in relevant
    ]

    current = risk.get("risk_score_current", risk.get("current", 0.0))
    potential = risk.get("risk_score_potential", risk.get("potential", 0.0))
    delta = risk.get("risk_score_delta", risk.get("delta", 0.0))

    summary = (
        f"CMS-HCC V28 RAF — current: {current}, potential: {potential}, delta: {delta}"
    )

    return RiskAssessment(
        id="risk-assessment-hcc",
        meta=Meta(profile=[DAVINCI_RISK_ASSESSMENT]),
        status="final",
        subject=_patient_reference(models),
        method=CodeableConcept(text="CMS-HCC V28"),
        code=CodeableConcept(text="CMS-HCC V28 Risk Adjustment"),
        prediction=predictions or None,
        note=[Annotation(text=summary)],
    )


def _validate_bundle(bundle_dict: dict[str, Any], models: dict[str, Any]) -> tuple[bool, list[str]]:
    Bundle = models["Bundle"]
    errors: list[str] = []
    try:
        bundle_json = json.dumps(bundle_dict)
        parsed = Bundle.model_validate_json(bundle_json)
        Bundle.model_validate_json(parsed.json())
        return True, errors
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))
        return False, errors


def to_fhir_bundle(
    demographics: dict[str, Any],
    key_problems: list[dict[str, Any]],
    medications: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    risk: dict[str, Any],
    *,
    vitals: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], bool, list[str]]:
    """Build a FHIR R4 collection Bundle and validate it."""
    models = _load_fhir_models()
    Bundle = models["Bundle"]
    BundleEntry = models["BundleEntry"]

    entries: list[Any] = []
    patient = _build_patient(demographics, models)
    entries.append(BundleEntry(resource=patient))

    condition_idx = 0
    for entity in key_problems:
        icd10 = entity.get("icd10")
        if not icd10:
            continue
        condition_idx += 1
        entries.append(BundleEntry(resource=_build_condition(entity, models, condition_idx)))

    med_idx = 0
    seen_rxnorm: set[str] = set()
    for entity in medications:
        rxnorm = entity.get("rxnorm")
        if not rxnorm:
            continue
        key = str(rxnorm)
        if key in seen_rxnorm:
            continue
        seen_rxnorm.add(key)
        med_idx += 1
        entries.append(BundleEntry(resource=_build_medication(entity, models, med_idx)))

    vital_idx = 0
    for entity in vitals or []:
        vital_idx += 1
        entries.append(BundleEntry(resource=_build_observation(entity, models, vital_idx)))

    risk_resource = _build_risk_assessment(gaps, risk, models)
    if risk_resource is not None:
        entries.append(BundleEntry(resource=risk_resource))

    bundle = Bundle(
        id=f"chartscope-bundle-{uuid4()}",
        type="collection",
        entry=entries,
    )
    bundle_dict = json.loads(bundle.json(exclude_none=True))
    valid, errors = _validate_bundle(bundle_dict, models)
    return bundle_dict, valid, errors
