# ChartScope

ChartScope is a clinical NLP application that reads unstructured clinical notes and turns them into structured, actionable output. Paste a note, optionally add the ICD-10 codes already on the claim, and the app will de-identify the text, pull out problems and medications, map them to standard codes, flag HCC coding gaps, and export a [FHIR](https://www.hl7.org/fhir/) bundle you can inspect in the UI.

Built for risk adjustment workflows ([CMS-HCC V28](https://www.cms.gov/medicare/health-plans/medicareadvtgspecratestats/risk-adjustors)), but the pipeline is modular enough to reuse for other clinical NLP tasks.

## What you get

- **De-identification** with [Microsoft Presidio](https://microsoft.github.io/presidio/) (PHI masked before anything else runs)
- **Clinical NER** via [Hugging Face](https://huggingface.co/) ([`d4data/biomedical-ner-all`](https://huggingface.co/d4data/biomedical-ner-all) by default)
- **Assertion detection** with [medspaCy ConText](https://github.com/medspacy/medspacy) (negation, history, family history)
- **Terminology linking** to [ICD-10](https://www.cms.gov/medicare/coding-billing/icd-10-codes) and [RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/) using [SapBERT](https://huggingface.co/cambridgeltl/SapBERT-from-PubMedBERT-fulltext) + lexical reranking
- **HCC gap detection** with RAF score comparison (current vs. potential) via [hccinfhir](https://pypi.org/project/hccinfhir/)
- **FHIR R4 export** aligned with [US Core](https://hl7.org/fhir/us/core/) and [Da Vinci](https://build.fhir.org/ig/HL7/davinci-ra/) risk assessment profiles
- **Evaluation tab** showing fine-tuned NER benchmark metrics

The web UI has four result tabs: entity extraction, coding gaps, FHIR, and model evaluation.

## How the pipeline works

When you hit Analyze, the backend runs these steps in order:

1. **De-ID:** mask names, dates, MRNs, and other PHI ([`deid.py`](./backend/app/pipeline/deid.py))
2. **Ingest:** clean the text and detect clinical sections ([`ingest.py`](./backend/app/pipeline/ingest.py))
3. **NER:** extract problems, medications, vitals, procedures, and tests ([`ner.py`](./backend/app/pipeline/ner.py))
4. **Context:** mark negated, historical, or family-history mentions as inactive ([`context.py`](./backend/app/pipeline/context.py))
5. **Linking:** map problems to ICD-10 and medications to RxNorm ([`linking.py`](./backend/app/pipeline/linking.py))
6. **HCC gaps:** compare note evidence against claimed codes and compute RAF impact ([`hcc.py`](./backend/app/pipeline/hcc.py))
7. **FHIR:** build and validate a collection Bundle ([`fhir_export.py`](./backend/app/pipeline/fhir_export.py))

Orchestration lives in [`backend/app/api/routes.py`](./backend/app/api/routes.py).

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

Then open [http://localhost:5173](http://localhost:5173). The API lives at [http://localhost:8000](http://localhost:8000) ([FastAPI](https://fastapi.tiangolo.com/) auto-docs at [http://localhost:8000/docs](http://localhost:8000/docs)).

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

Copy [`backend/.env.example`](./backend/.env.example) to `backend/.env` if you want to override app name, version, or CORS origins.

Health check: [`GET /api/health`](http://localhost:8000/api/health)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The [Vite](https://vitejs.dev/) dev server proxies `/api` to the backend (default `http://localhost:8000`). See [`frontend/.env.example`](./frontend/.env.example) to change the proxy target.

### Run tests

From the `backend` directory:

```bash
pytest
```

Tests live in [`backend/tests/`](./backend/tests/) and cover de-ID, NER, linking, HCC gap logic, FHIR export, and data loaders.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Run the full pipeline |
| `GET` | `/api/examples` | Curated synthetic example notes |
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

The response includes de-identified text, entities, key problems, HCC gaps, RAF scores, demographics, and a FHIR bundle with a validation flag. Request/response shapes are defined in [`backend/app/models/schemas.py`](./backend/app/models/schemas.py).

## Sample data

ChartScope only uses **synthetic or public-domain data**. See [DATA_GOVERNANCE.md](./DATA_GOVERNANCE.md) for the full policy.

| Source | What it's for |
|--------|---------------|
| **Built-in examples** | Three synthetic notes with deliberate coding gaps ([`examples.py`](./backend/app/pipeline/examples.py)) |
| **[Synthea](https://synthea.mitre.org/)** | 12 bundled FHIR patient bundles in [`backend/app/data/synthea/`](./backend/app/data/synthea/) |
| **[MTSamples](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions)** | Public de-identified transcriptions for the random-note picker |
| **User input** | Anything you paste into the text box |

### MTSamples (optional)

The random-note picker expects a CSV at:

```
backend/app/data/raw/mtsamples.csv
```

That file is not bundled in the repo. Download the [MTSamples dataset on Kaggle](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions) and place the CSV at the path above. The built-in examples work without it.

### Synthea refresh

To regenerate or expand Synthea fixtures:

```bash
cd backend
python -m app.data.get_synthea
```

See [`backend/app/data/get_synthea.py`](./backend/app/data/get_synthea.py) for download URLs and fallback generation.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `CHARTSCOPE_NER_MODEL` | [`d4data/biomedical-ner-all`](https://huggingface.co/d4data/biomedical-ner-all) | Hugging Face NER model |
| `CHARTSCOPE_LINK_THRESHOLD` | `0.55` | Min link score for HCC evidence |
| `APP_NAME` | `ChartScope` | API title |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed frontend origins |

## NER fine-tuning (offline)

There is a separate training track for fine-tuning [PubMedBERT](https://huggingface.co/microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract) on the public [NCBI-Disease](https://huggingface.co/datasets/ncbi/ncbi_disease) corpus and benchmarking it against the live baseline. Metrics land in [`backend/eval/finetune_metrics.json`](./backend/eval/finetune_metrics.json) and show up in the Evaluation tab.

See [backend/training/README.md](./backend/training/README.md) for setup, the [Colab notebook](./backend/training/finetune_ner_colab.ipynb), and how to wire a fine-tuned model into inference.

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

**Backend:** [FastAPI](https://fastapi.tiangolo.com/), [spaCy](https://spacy.io/), [medspaCy](https://github.com/medspacy/medspacy), [Presidio](https://microsoft.github.io/presidio/), [Hugging Face Transformers](https://huggingface.co/docs/transformers/), [SapBERT](https://huggingface.co/cambridgeltl/SapBERT-from-PubMedBERT-fulltext), [hccinfhir](https://pypi.org/project/hccinfhir/), [fhir.resources](https://pypi.org/project/fhir-resources/)

**Frontend:** [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/), [Recharts](https://recharts.org/)

## Contributing

Do not commit real PHI, credentialed datasets ([MIMIC](https://mimic.mit.edu/), [n2c2](https://portal.dbmi.hms.harvard.edu/projects/n2c2-nlp/), [i2b2](https://www.i2b2.org/)), or patient data. If you are unsure whether a dataset is allowed, check [DATA_GOVERNANCE.md](./DATA_GOVERNANCE.md) first.
