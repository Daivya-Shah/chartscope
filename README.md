# ChartScope

Advanced clinical NLP web application for de-identification, entity extraction, HCC gap detection, and FHIR export — built for healthcare data science workflows.

## Problem

Clinical documentation is unstructured free text. Payers and providers need automated tools to:

- Redact PHI before downstream processing
- Extract conditions, medications, and symptoms with clinical context (negation, temporality)
- Identify HCC coding gaps that affect risk adjustment
- Export structured FHIR bundles for interoperability

ChartScope provides a modular pipeline and product-grade UI to address these needs using **only synthetic and public-domain data**.

## Architecture

Monorepo with a typed JSON API boundary between frontend and backend.

```
chartscope/
├── backend/          FastAPI + clinical NLP pipeline
│   ├── app/
│   │   ├── main.py           Entry point, CORS, /api/health
│   │   ├── api/routes.py     REST endpoints
│   │   ├── models/schemas.py Pydantic v2 request/response models
│   │   └── pipeline/         Modular NLP stages (stubs in scaffold)
│   ├── eval/                 Offline evaluation harness
│   └── tests/                pytest suite
├── frontend/         Vite + React 18 + TypeScript + Tailwind
│   └── src/
│       ├── lib/api.ts        Typed axios client
│       ├── types/api.ts      TS types mirroring backend schemas
│       └── components/       Product UI (AppShell, panels)
└── docker-compose.yml
```

### Endpoint Map

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Service health check |
| POST | `/api/analyze` | Run full NLP pipeline on a note |
| GET | `/api/examples` | Curated example notes |
| GET | `/api/mtsamples/random` | Random MTSamples transcription |
| GET | `/api/eval` | Pipeline evaluation metrics |

### Component Map

| Component | Role |
|-----------|------|
| `AppShell` | Header, layout, compliance badge, backend status |
| `NoteInput` | Paste/load clinical notes |
| `EntityHighlighter` | NER entity visualization |
| `GapsPanel` | HCC gap analysis results |
| `FhirViewer` | FHIR Bundle JSON viewer |
| `EvalDashboard` | Model evaluation metrics |

## Tech Stack

**Backend:** Python 3.11, FastAPI, uvicorn, Pydantic v2, pandas

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, axios, lucide-react, recharts

**Pipeline (planned):** spaCy, scispaCy, medspaCy, Presidio, fhir.resources, hccinfhir, transformers

## Data Governance

> **Hard compliance rule:** The deployed/public app may **ONLY** process synthetic or public-domain data (Synthea, MTSamples, user-pasted text). **NEVER** add MIMIC, n2c2, or i2b2 data to this repo or any deployment — those are credentialed/DUA-restricted and reserved for **offline training only**.

See [DATA_GOVERNANCE.md](./DATA_GOVERNANCE.md) for full policy and enforcement details.

## Local Dev

### Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) Docker & Docker Compose

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Verify: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — the header should show **Backend connected** (green dot).

The Vite dev server proxies `/api` → `http://localhost:8000`.

### Docker Compose

```bash
docker compose up --build
```

- Backend: [http://localhost:8000](http://localhost:8000)
- Frontend: [http://localhost:5173](http://localhost:5173)

### Tests

```bash
cd backend
pytest tests/ -v
```

## Roadmap

1. **NER** — Fine-tuned Bio_ClinicalBERT on n2c2 annotations (offline training; weights only in repo)
2. **HCC scoring** — Real RAF calculation via hccinfhir with ICD-10 → HCC mapping
3. **FHIR export** — Bundles aligned to US Core Condition/Medication profiles and Da Vinci PDex
4. **De-identification** — Presidio-based PHI detection tuned for clinical notes
5. **Evaluation** — Automated harness with gold-standard fixtures from Synthea

## License

Interview / portfolio project — not for production clinical use.
