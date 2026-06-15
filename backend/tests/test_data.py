"""Tests for ChartScope data loaders and curated examples."""

import pytest

from app.data.loaders import (
    get_random_note,
    is_valid_icd10,
    load_mtsamples,
    load_synthea_patients,
)
from app.pipeline.examples import EXAMPLE_NOTES


def test_load_mtsamples_non_empty_with_transcriptions():
    df = load_mtsamples()
    assert len(df) > 0
    assert "transcription" in df.columns
    assert df["transcription"].str.len().min() > 0


def test_get_random_note_cardiovascular_pulmonary():
    note = get_random_note("Cardiovascular / Pulmonary")
    assert note["specialty"].casefold() == "cardiovascular / pulmonary".casefold()
    assert len(note["transcription"]) > 0
    assert note["sample_id"]


def test_load_synthea_patients():
    patients = load_synthea_patients()
    assert len(patients) >= 10
    for patient in patients:
        assert patient.get("patient_id")
        assert len(patient.get("claimed_conditions", [])) >= 1
        for cond in patient["claimed_conditions"]:
            assert is_valid_icd10(cond["icd10"]), f"Invalid ICD-10: {cond['icd10']}"


def test_example_notes():
    assert len(EXAMPLE_NOTES) == 3
    for note in EXAMPLE_NOTES:
        assert note.note_text.strip()
        assert isinstance(note.claimed_codes, list)
        assert len(note.claimed_codes) >= 1
