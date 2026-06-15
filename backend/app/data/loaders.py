"""Data loaders for MTSamples CSV and Synthea FHIR Bundles.

All paths are resolved relative to this module file, not the process CWD.
"""

from __future__ import annotations

import json
import random
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
MTSAMPLES_PATH = DATA_DIR / "raw" / "mtsamples.csv"
SYNTHEA_DIR = DATA_DIR / "synthea"

_mtsamples_cache: pd.DataFrame | None = None
_synthea_cache: list[dict[str, Any]] | None = None

ICD10_PATTERN = re.compile(r"^[A-Z]\d{2}(\.\d{1,4})?$")


def _require_mtsamples_path() -> Path:
    if not MTSAMPLES_PATH.is_file():
        raise FileNotFoundError(f"MTSamples CSV not found at {MTSAMPLES_PATH}")
    return MTSAMPLES_PATH


def load_mtsamples() -> pd.DataFrame:
    """Load and cache MTSamples CSV; returns normalized DataFrame."""
    global _mtsamples_cache
    if _mtsamples_cache is not None:
        return _mtsamples_cache

    path = _require_mtsamples_path()
    raw = pd.read_csv(path, dtype=str)

    # First column is the row index from the export.
    if raw.columns[0].startswith("Unnamed") or raw.columns[0] == "":
        raw = raw.rename(columns={raw.columns[0]: "index"})

    df = pd.DataFrame(
        {
            "sample_id": raw["index"].astype(str).str.strip(),
            "specialty": raw["medical_specialty"].fillna("").str.strip(),
            "description": raw["description"].fillna("").str.strip(),
            "sample_name": raw["sample_name"].fillna("").str.strip(),
            "transcription": raw["transcription"].fillna("").str.strip(),
        }
    )
    df = df[df["transcription"].str.len() > 0].reset_index(drop=True)
    _mtsamples_cache = df
    return _mtsamples_cache


def get_random_note(specialty: str | None = None) -> dict[str, str]:
    """Return one random MTSamples transcription, optionally filtered by specialty."""
    df = load_mtsamples()
    if specialty is not None:
        needle = specialty.strip().casefold()
        filtered = df[df["specialty"].str.casefold() == needle]
        if filtered.empty:
            raise ValueError(f"No MTSamples notes found for specialty: {specialty!r}")
        df = filtered

    row = df.sample(n=1).iloc[0]
    return {
        "sample_id": row["sample_id"],
        "specialty": row["specialty"],
        "description": row["description"],
        "transcription": row["transcription"],
    }


def list_specialties() -> list[dict[str, str | int]]:
    """Return specialties with note counts, sorted by count descending."""
    df = load_mtsamples()
    counts = (
        df.groupby("specialty", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )
    return [
        {"specialty": row["specialty"], "count": int(row["count"])}
        for _, row in counts.iterrows()
        if row["specialty"]
    ]


def _patient_age(patient: dict[str, Any], today: date | None = None) -> int | None:
    birth_date = patient.get("birthDate")
    if not birth_date:
        return None
    try:
        born = datetime.strptime(birth_date[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    ref = today or date.today()
    return ref.year - born.year - ((ref.month, ref.day) < (born.month, born.day))


def _extract_icd10(condition: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    code_obj = condition.get("code") or {}
    for coding in code_obj.get("coding") or []:
        system = (coding.get("system") or "").casefold()
        if "icd-10" in system or "icd10" in system:
            icd10 = coding.get("code")
            display = coding.get("display")
            status = None
            clinical = condition.get("clinicalStatus") or {}
            status_codings = clinical.get("coding") or []
            if status_codings:
                status = status_codings[0].get("code")
            return icd10, display, status
    return None, None, None


def _parse_synthea_bundle(bundle: dict[str, Any]) -> dict[str, Any] | None:
    if bundle.get("resourceType") != "Bundle":
        return None

    patient: dict[str, Any] | None = None
    conditions: list[dict[str, Any]] = []

    for entry in bundle.get("entry") or []:
        resource = entry.get("resource") or {}
        rtype = resource.get("resourceType")
        if rtype == "Patient" and patient is None:
            patient = resource
        elif rtype == "Condition":
            icd10, display, clinical_status = _extract_icd10(resource)
            if icd10:
                conditions.append(
                    {
                        "icd10": icd10,
                        "display": display or icd10,
                        "clinical_status": clinical_status or "active",
                    }
                )

    if patient is None:
        return None

    patient_id = patient.get("id") or "unknown"
    sex = patient.get("gender") or "unknown"
    age = _patient_age(patient)

    note_lines = [
        f"SYNTHETIC PATIENT SUMMARY — id {patient_id}, age {age}, sex {sex}.",
        "Claimed conditions on record:",
    ]
    for cond in conditions:
        note_lines.append(f"- {cond['display']} ({cond['icd10']}), status {cond['clinical_status']}")

    return {
        "patient_id": patient_id,
        "age": age,
        "sex": sex,
        "claimed_conditions": conditions,
        "note_text": "\n".join(note_lines),
    }


def load_synthea_patients() -> list[dict[str, Any]]:
    """Load and cache parsed Synthea patient summaries from FHIR Bundles."""
    global _synthea_cache
    if _synthea_cache is not None:
        return _synthea_cache

    if not SYNTHEA_DIR.is_dir():
        raise FileNotFoundError(
            f"Synthea directory not found at {SYNTHEA_DIR}. Run get_synthea.py first."
        )

    patients: list[dict[str, Any]] = []
    for path in sorted(SYNTHEA_DIR.glob("*.json")):
        try:
            bundle = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        parsed = _parse_synthea_bundle(bundle)
        if parsed and parsed["claimed_conditions"]:
            patients.append(parsed)

    _synthea_cache = patients
    return _synthea_cache


def is_valid_icd10(code: str) -> bool:
    """Return True if code matches a basic ICD-10-CM pattern."""
    return bool(ICD10_PATTERN.match(code.strip().upper()))
