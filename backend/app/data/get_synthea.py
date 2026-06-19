"""Populate backend/app/data/synthea/ with synthetic FHIR R4 patient Bundles.

Primary path: download MITRE Synthea 100-patient FHIR R4 sample zip.
Fallback: built-in generator (~12 fully synthetic Bundles in code).

Idempotent — skips work when >= MIN_BUNDLES JSON files already exist.
Run: python -m app.data.get_synthea   (from backend/)
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import uuid
import zipfile
from datetime import date, timedelta
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).resolve().parent
SYNTHEA_DIR = DATA_DIR / "synthea"
MIN_BUNDLES = 10
TARGET_BUNDLES = 12

# MITRE Synthea sample data (100 patients, FHIR R4) — may require browser UA.
DOWNLOAD_URLS = [
    "https://synthea.mitre.org/downloads/synthea_sample_data_fhir_latest.zip",
    "https://syntheticmass.mitre.org/downloads/synthea_sample_data_fhir_latest.zip",
]

HTTP_HEADERS = {
    "User-Agent": "ChartScope/0.1 (synthetic-data-setup; https://github.com/chartscope)",
    "Accept": "*/*",
}

# Chronic conditions for the built-in fallback generator (all synthetic).
FALLBACK_CONDITIONS = [
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("E11.22", "Type 2 diabetes mellitus with diabetic chronic kidney disease"),
    ("E11.42", "Type 2 diabetes mellitus with diabetic polyneuropathy"),
    ("I50.22", "Chronic systolic (congestive) heart failure"),
    ("I50.32", "Chronic diastolic (congestive) heart failure"),
    ("J44.1", "Chronic obstructive pulmonary disease with acute exacerbation"),
    ("J44.9", "Chronic obstructive pulmonary disease, unspecified"),
    ("N18.3", "Chronic kidney disease, stage 3"),
    ("N18.4", "Chronic kidney disease, stage 4"),
    ("I10", "Essential (primary) hypertension"),
    ("F32.1", "Major depressive disorder, single episode, moderate"),
    ("F32.9", "Major depressive disorder, single episode, unspecified"),
    ("E78.5", "Hyperlipidemia, unspecified"),
    ("I25.10", "Atherosclerotic heart disease of native coronary artery without angina pectoris"),
]


def _existing_bundle_count() -> int:
    if not SYNTHEA_DIR.is_dir():
        return 0
    return len(list(SYNTHEA_DIR.glob("*.json")))


def _write_bundle(path: Path, bundle: dict) -> None:
    path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")


def _make_patient_bundle(
    patient_index: int,
    sex: str,
    age: int,
    condition_specs: list[tuple[str, str]],
) -> dict:
    """Build a fully synthetic FHIR R4 collection Bundle."""
    patient_id = str(uuid.uuid4())
    birth = date.today() - timedelta(days=age * 365 + patient_index * 11)
    patient_resource = {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"],
            "tag": [
                {
                    "system": "http://chartscope.local/tags",
                    "code": "synthetic",
                    "display": "Fully synthetic — ChartScope built-in generator",
                }
            ],
        },
        "identifier": [
            {
                "system": "urn:chartscope:synthetic",
                "value": f"SYN-{patient_index:03d}",
            }
        ],
        "gender": sex,
        "birthDate": birth.isoformat(),
        "deceasedBoolean": False,
        "name": [
            {
                "use": "official",
                "family": f"SyntheticPatient{patient_index:03d}",
                "given": ["ChartScope", "Synthetic"],
            }
        ],
    }

    entries: list[dict] = [
        {
            "fullUrl": f"urn:uuid:{patient_id}",
            "resource": patient_resource,
        }
    ]

    for icd10, display in condition_specs:
        cond_id = str(uuid.uuid4())
        entries.append(
            {
                "fullUrl": f"urn:uuid:{cond_id}",
                "resource": {
                    "resourceType": "Condition",
                    "id": cond_id,
                    "meta": {
                        "tag": [
                            {
                                "system": "http://chartscope.local/tags",
                                "code": "synthetic",
                                "display": "Fully synthetic condition",
                            }
                        ]
                    },
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active",
                            }
                        ]
                    },
                    "verificationStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                                "code": "confirmed",
                            }
                        ]
                    },
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                                    "code": "encounter-diagnosis",
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                                "code": icd10,
                                "display": display,
                            }
                        ],
                        "text": display,
                    },
                    "subject": {"reference": f"urn:uuid:{patient_id}"},
                },
            }
        )

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": date.today().isoformat(),
        "identifier": {
            "system": "urn:chartscope:synthea",
            "value": f"synthetic-bundle-{patient_index:03d}",
        },
        "entry": entries,
    }


def generate_builtin_bundles() -> int:
    """Create TARGET_BUNDLES synthetic FHIR R4 Bundles in SYNTHEA_DIR."""
    SYNTHEA_DIR.mkdir(parents=True, exist_ok=True)
    sexes = ["male", "female"]
    ages = [58, 62, 67, 71, 74, 78, 63, 69, 76, 81, 55, 85]

    written = 0
    for i in range(TARGET_BUNDLES):
        # Assign 2–5 conditions per patient, cycling through the chronic set.
        n_conds = 2 + (i % 4)
        conds = [
            FALLBACK_CONDITIONS[(i * 3 + j) % len(FALLBACK_CONDITIONS)]
            for j in range(n_conds)
        ]
        bundle = _make_patient_bundle(
            patient_index=i + 1,
            sex=sexes[i % len(sexes)],
            age=ages[i % len(ages)],
            condition_specs=conds,
        )
        out_path = SYNTHEA_DIR / f"synthetic-patient-{i + 1:03d}.json"
        _write_bundle(out_path, bundle)
        written += 1

    return written


def _java_available() -> bool:
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _download_and_extract(max_files: int = 40) -> int:
    """Attempt to download Synthea sample zip and extract JSON bundles."""
    SYNTHEA_DIR.mkdir(parents=True, exist_ok=True)

    for url in DOWNLOAD_URLS:
        try:
            with httpx.Client(timeout=120.0, follow_redirects=True, headers=HTTP_HEADERS) as client:
                response = client.get(url)
                if response.status_code != 200:
                    continue
                content = response.content
                if len(content) < 1000:
                    continue
        except httpx.HTTPError:
            continue

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                json_names = [n for n in zf.namelist() if n.lower().endswith(".json")]
                if not json_names:
                    continue
                extracted = 0
                for name in json_names[:max_files]:
                    data = zf.read(name)
                    try:
                        bundle = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    if bundle.get("resourceType") != "Bundle":
                        continue
                    dest = SYNTHEA_DIR / Path(name).name
                    dest.write_bytes(data)
                    extracted += 1
                if extracted >= MIN_BUNDLES:
                    return extracted
        except zipfile.BadZipFile:
            continue

    return 0


def _run_synthea_jar() -> int:
    """Run Synthea JAR if Java is available (best-effort)."""
    if not _java_available():
        return 0

    work_dir = DATA_DIR / "_synthea_run"
    work_dir.mkdir(parents=True, exist_ok=True)
    jar_path = work_dir / "synthea-with-dependencies.jar"
    output_fhir = work_dir / "output" / "fhir"

    jar_url = (
        "https://github.com/synthetichealth/synthea/releases/download/"
        "master-branch-latest/synthea-with-dependencies.jar"
    )

    try:
        if not jar_path.is_file():
            with httpx.Client(timeout=300.0, follow_redirects=True, headers=HTTP_HEADERS) as client:
                resp = client.get(jar_url)
                if resp.status_code != 200:
                    return 0
                jar_path.write_bytes(resp.content)

        subprocess.run(
            [
                "java",
                "-jar",
                str(jar_path),
                "-p",
                str(TARGET_BUNDLES),
                "--exporter.baseDirectory",
                str(work_dir / "output"),
                "--exporter.fhir.export=true",
            ],
            check=True,
            capture_output=True,
            timeout=600,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, httpx.HTTPError, OSError):
        return 0

    if not output_fhir.is_dir():
        return 0

    SYNTHEA_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in sorted(output_fhir.glob("*.json"))[:40]:
        shutil.copy2(src, SYNTHEA_DIR / src.name)
        copied += 1
    return copied


def populate_synthea() -> str:
    """Populate SYNTHEA_DIR; return a human-readable description of the path used."""
    existing = _existing_bundle_count()
    if existing >= MIN_BUNDLES:
        print(f"[get_synthea] Already populated ({existing} bundles in {SYNTHEA_DIR}). Skipping.")
        return "existing"

    print(f"[get_synthea] Populating {SYNTHEA_DIR} …")

    count = _download_and_extract()
    if count >= MIN_BUNDLES:
        print(f"[get_synthea] Used MITRE Synthea sample download ({count} bundles).")
        return "download"

    if _java_available():
        count = _run_synthea_jar()
        if count >= MIN_BUNDLES:
            print(f"[get_synthea] Used local Synthea JAR generation ({count} bundles).")
            return "java"

    count = generate_builtin_bundles()
    print(
        f"[get_synthea] Used built-in synthetic generator ({count} fully synthetic bundles). "
        "All patients labeled synthetic — no real PHI."
    )
    return "builtin"


def main() -> None:
    path_used = populate_synthea()
    final_count = _existing_bundle_count()
    print(f"[get_synthea] Done. path={path_used!r}, bundles={final_count}, dir={SYNTHEA_DIR}")


if __name__ == "__main__":
    main()
