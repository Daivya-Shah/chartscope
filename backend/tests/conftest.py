"""Pytest configuration — ensure Synthea synthetic data exists before data tests."""

from app.data.get_synthea import MIN_BUNDLES, SYNTHEA_DIR, populate_synthea


def pytest_sessionstart(session):
    existing = len(list(SYNTHEA_DIR.glob("*.json"))) if SYNTHEA_DIR.is_dir() else 0
    if existing < MIN_BUNDLES:
        populate_synthea()
