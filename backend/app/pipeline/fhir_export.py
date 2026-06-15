# TODO (build step: fhir): FHIR R4 Bundle export aligned to US Core / Da Vinci PDex


def build_fhir_bundle(entities: list[dict], gaps: list[dict]) -> dict:
    """Stub: return minimal FHIR Bundle skeleton."""
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [],
    }
