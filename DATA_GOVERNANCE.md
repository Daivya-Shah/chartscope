# ChartScope Data Governance

## Hard Compliance Rule

**The deployed/public ChartScope application may ONLY ever process synthetic or public-domain data.**

Permitted data sources:

| Source | Type | Usage |
|--------|------|-------|
| **Synthea** | Synthetic FHIR/CSV | Bundled sample patients, eval fixtures |
| **MTSamples** | Public-domain de-identified transcriptions | Example notes, random-note picker |
| **User-pasted text** | User-provided | Manual input in the UI |

## Prohibited Data

The following credentialed, DUA-restricted datasets **must never** be added to this repository, any deployment, or any public-facing environment:

- **MIMIC-III / MIMIC-IV** (PhysioNet credentialed access)
- **n2c2** (National NLP Clinical Challenges — restricted use agreements)
- **i2b2** (Informatics for Integrating Biology & the Bedside — restricted)

These datasets are reserved exclusively for **offline model training** on a local, credentialed workstation. Training artifacts (fine-tuned weights) may be referenced in the roadmap but the raw data itself must never enter this repo.

## Enforcement

1. `.gitignore` blocks common restricted-data file patterns from being committed.
2. All API endpoints in this scaffold return synthetic or MTSamples-derived placeholder data only.
3. CI (future) should include a restricted-data filename scan.
4. Contributors must not paste real PHI/PII into issues, PRs, or commit messages.
5. De-identification targets HIPAA Safe Harbor identifiers and intentionally preserves ages under 90 and clinical durations to retain clinical meaning.

## Offline Training Roadmap (Not in This Repo)

Fine-tuned Bio_ClinicalBERT NER models trained on n2c2/i2b2 annotations will be developed offline. Only the exported model weights (`.bin`/`.safetensors`) and eval metrics may be committed — never the source annotations or raw notes.

## Contact

If you have questions about whether a dataset is permitted, assume it is **not** until verified against this document.
