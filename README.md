# ChartScope

ChartScope is a clinical NLP demo that reads unstructured clinical notes and turns them into structured, actionable output. Paste a note, optionally add the ICD-10 codes already on the claim, and the app will de-identify the text, pull out problems and medications, map them to standard codes, flag HCC coding gaps, and export a FHIR bundle you can inspect in the UI.

Built for risk adjustment workflows (CMS-HCC V28), but the pipeline is modular enough to reuse for other clinical NLP tasks.

## What you get

- **De-identification** with Microsoft Presidio (PHI masked before anything else runs)
- **Clinical NER** via Hugging Face (`d4data/biomedical-ner-all` by default)
- **Assertion detection** with medspaCy ConText (negation, history, family history)
- **Terminology linking** to ICD-10 and RxNorm using SapBERT + lexical reranking
- **HCC gap detection** with RAF score comparison (current vs. potential)
- **FHIR R4 export** aligned with US Core and Da Vinci risk assessment profiles
- **Evaluation tab** showing fine-tuned NER benchmark metrics

The web UI has four result tabs: entity extraction, coding gaps, FHIR, and model evaluation.

## How the pipeline works

When you hit Analyze, the backend runs these steps in order:

1. **De-ID:** mask names, dates, MRNs, and other PHI
2. **Ingest:** clean the text and detect clinical sections (Assessment, Plan, etc.)
3. **NER:** extract problems, medications, vitals, procedures, and tests
4. **Context:** mark negated, historical, or family-history mentions as inactive
5. **Linking:** map problems to ICD-10 and medications to RxNorm
6. **HCC gaps:** compare note evidence against claimed codes and compute RAF impact
7. **FHIR:** build and validate a collection Bundle

Gap statuses:

| Status | Meaning |
|--------|---------|
| **suspected** | Documented in the note but missing from the claim |
| **confirmed** | Documented and already on the claim |
| **unsupported** | On the claim but not supported by the note |
| **superseded** | A more specific code in the note would upgrade the HCC |

## Quick start (Docker)

The fastest way to run everything:

```bash
docker compose up --build
```

Then open [http://localhost:5173](http://localhost:5173). The API lives at [http://localhost:8000](http://localhost:8000).

**Note:** The first analysis request can take a while. Hugging Face models download on first use, and SapBERT builds ICD-10 embedding cache files on disk.

## Local development

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg

uvicorn app.main:app --reload --port 8000
```

Copy `backend/.env.example` to `backend/.env` if you want to override app name, version, or CORS origins.

Health check: `GET http://localhost:8000/api/health`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to the backend (default `http://localhost:8000`). See `frontend/.env.example` to change the proxy target.

### Run tests

From the `backend` directory:

```bash
pytest
```

Tests cover de-ID, NER, linking, HCC gap logic, FHIR export, and data loaders.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Run the full pipeline |
| `GET` | `/api/examples` | Curated synthetic demo notes |
| `GET` | `/api/mtsamples/random` | Random public-domain note (optional specialty filter) |
| `GET` | `/api/mtsamples/specialties` | Available MTSamples specialties |
| `GET` | `/api/eval` | NER fine-tune benchmark metrics |

### Analyze request

```json
{
  "note_text": "68-year-old male with type 2 diabetes...",
  "claimed_codes": ["E11.9", "I10"]
}
```

The response includes de-identified text, entities, key problems, HCC gaps, RAF scores, demographics, and a FHIR bundle with a validation flag.

## Sample data

ChartScope only uses **synthetic or public-domain data**. See [DATA_GOVERNANCE.md](./DATA_GOVERNANCE.md) for the full policy.

| Source | What it's for |
|--------|---------------|
| **Built-in examples** | Three synthetic notes with deliberate coding gaps (load from the UI) |
| **Synthea** | 12 bundled FHIR patient bundles in `backend/app/data/synthea/` |
| **MTSamples** | Public de-identified transcriptions for the random-note picker |
| **User input** | Anything you paste into the text box |

### MTSamples (optional)

The random-note picker expects a CSV at:

```
backend/app/data/raw/mtsamples.csv
```

That file is not bundled in the repo. Download the [MTSamples dataset](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions) and place the CSV at the path above. The built-in examples work without it.

### Synthea refresh

To regenerate or expand Synthea fixtures:

```bash
cd backend
python -m app.data.get_synthea
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `CHARTSCOPE_NER_MODEL` | `d4data/biomedical-ner-all` | Hugging Face NER model |
| `CHARTSCOPE_LINK_THRESHOLD` | `0.55` | Min link score for HCC evidence |
| `APP_NAME` | `ChartScope` | API title |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed frontend origins |

## NER fine-tuning (offline)

There is a separate training track for fine-tuning PubMedBERT on the public NCBI-Disease corpus and benchmarking it against the live baseline. Metrics land in `backend/eval/finetune_metrics.json` and show up in the Evaluation tab.

See [backend/training/README.md](./backend/training/README.md) for setup, Colab notebook, and how to wire a fine-tuned model into inference.

## Project structure

```
chartscope/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── api/routes.py     # REST endpoints
│   │   ├── models/schemas.py # Request/response models
│   │   ├── pipeline/         # De-ID, NER, linking, HCC, FHIR
│   │   └── data/             # Terminology CSVs, Synthea, loaders
│   ├── training/             # Offline NER fine-tuning
│   ├── eval/                 # Benchmark metrics JSON
│   └── tests/
├── frontend/
│   └── src/                  # React UI
├── docker-compose.yml
└── DATA_GOVERNANCE.md
```

## Tech stack

**Backend:** FastAPI, spaCy, medspaCy, Presidio, Hugging Face Transformers, SapBERT, hccinfhir, fhir.resources

**Frontend:** React, TypeScript, Vite, Tailwind CSS, Recharts

## Contributing

Do not commit real PHI, credentialed datasets (MIMIC, n2c2, i2b2), or patient data. If you are unsure whether a dataset is allowed, check [DATA_GOVERNANCE.md](./DATA_GOVERNANCE.md) first.
