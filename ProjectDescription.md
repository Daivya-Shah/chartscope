# ChartScope: Project Description

ChartScope is a reference implementation of a clinical NLP system. It takes unstructured progress notes and produces de-identified text, terminology-linked clinical entities, HCC coding gap recommendations with RAF impact estimates, and a validated FHIR R4 bundle. Built as an interview and portfolio demo, it runs on synthetic and public-domain data only and is not intended for production clinical use.

## The Problem

Clinical detail lives in free-text notes, but risk adjustment and billing run on structured ICD-10 codes. Those codes feed CMS Hierarchical Condition Category (HCC) models that produce a Risk Adjustment Factor (RAF) score, which influences Medicare Advantage reimbursement. When documentation and claims diverge, organizations either miss legitimate HCC capture or carry unsupported codes that create audit risk. Regulatory pressure (CMS-0057, Da Vinci) also pushes health data exchange toward FHIR. ChartScope closes the loop from narrative text to coded, interoperable output.

## What It Does

A user submits a clinical note and optional claimed ICD-10 codes. The system returns four views: entity extraction with inline highlights, HCC coding gaps with RAF scores, a FHIR bundle, and offline NER evaluation metrics.

The backend runs a fixed-order pipeline. De-identification (Microsoft Presidio) masks HIPAA Safe Harbor identifiers first; clinically useful ages and durations are preserved. The note is cleaned and split into sections (Assessment, Plan, etc.) via medspaCy. A biomedical NER model extracts problems, medications, procedures, tests, anatomy, and vitals. ConText assertion detection filters out negated, historical, family, and uncertain problem mentions. Active problems link to ICD-10-CM via SapBERT embeddings plus lexical matching; medications link to RxNorm via local dictionary and RxNav fallback. Age and sex are parsed from the note for RAF calculations.

Gap detection compares note-evidenced HCCs against HCCs implied by claimed codes using CMS-HCC Model V28 (via hccinfhir). High-confidence active problems in Assessment or Plan sections become evidence; vague symptom fragments are dropped. Each HCC receives one of four statuses:

**Suspected:** documented in the note but absent from the claim (e.g., heart failure in Assessment, only hypertension claimed).

**Confirmed:** documented and supported by a matching claimed code.

**Unsupported:** on the claim but not found in the note (compliance risk).

**Superseded:** claim uses a generic code, but the note supports a more specific diagnosis that maps to a higher HCC (e.g., diabetic CKD documented while only uncomplicated diabetes is claimed).

Current RAF uses claimed codes alone; potential RAF uses claimed plus note-evidenced codes. The delta quantifies uncaptured opportunity. Each gap carries MEAT-style evidence (mention plus section), confidence, and a recommendation.

Finally, outputs assemble into a validated FHIR R4 collection Bundle: Patient, US Core Conditions, MedicationStatements, Observations, and a Da Vinci RiskAssessment. All bundles use synthetic patient identity.

## User Experience

Users paste text, load curated synthetic examples (heart failure, diabetes with complications, COPD), or pull random MTSamples transcriptions. The Extraction tab shows de-identified text with entity highlights, assertion tags, and code links. Coding Gaps shows RAF current/potential/delta and status-grouped gap cards. FHIR shows the validated bundle. Evaluation compares fine-tuned PubMedBERT (F1 0.87) against the live baseline (F1 0.37) on NCBI-Disease, demonstrating why task-specific training matters even though fine-tuned weights are not yet wired into inference.

## Data Governance

Runtime data is limited to Synthea synthetics, MTSamples public transcriptions, hand-authored demo notes, and user-pasted text. Credentialed datasets (MIMIC, n2c2, i2b2) are prohibited in the repo and any public deployment; they are reserved for offline training where only exported weights and metrics may be committed.

## Limitations and Roadmap

Gap recommendations are algorithmic and require qualified clinical and coding review. Demographics parsing, terminology linking, and NER all have known failure modes on ambiguous or rare content. FHIR output is a demo artifact, not a clinical record.

Planned work includes credentialed-data fine-tuning (weights only), relation extraction for richer MEAT evidence, live-pipeline eval with gold fixtures, and deployment hardening.

## Technical Stack

**Backend:** Python 3.11+, FastAPI, Pydantic v2, uvicorn

**De-identification:** Microsoft Presidio, spaCy

**NER:** HuggingFace transformers, PyTorch (`d4data/biomedical-ner-all` inference; PubMedBERT fine-tune track)

**Clinical context:** medspaCy (ConText, Sectionizer)

**Terminology linking:** SapBERT, RapidFuzz, ICD-10-CM and RxNorm dictionaries, NLM RxNav API

**Risk adjustment:** hccinfhir (CMS-HCC Model V28)

**Interop:** fhir.resources R4B (US Core, Da Vinci RiskAssessment)

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, axios, lucide-react, recharts

**Eval/training:** datasets, seqeval, evaluate, accelerate

**Testing:** pytest (33 tests)

**Containerization:** Docker, docker-compose
