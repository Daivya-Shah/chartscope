# ChartScope NER Fine-Tuning Track

Offline training and benchmarking for clinical NER. This track fine-tunes **PubMedBERT** on the public [**NCBI-Disease**](https://huggingface.co/datasets/ncbi/ncbi_disease) corpus and compares it head-to-head against the ChartScope inference baseline (`d4data/biomedical-ner-all`).

## Data governance

| Dataset | Status | Notes |
|---------|--------|-------|
| **NCBI-Disease** | ✅ Public, no credentialing | Used here for fine-tuning and eval |
| **Synthea / MTSamples** | ✅ Public / synthetic | Used by the live app |
| **MIMIC / n2c2 / i2b2** | ❌ Offline-only | Never in this repo — see [DATA_GOVERNANCE.md](../../DATA_GOVERNANCE.md) |

Metrics are written to `backend/eval/finetune_metrics.json` for the future eval dashboard (`GET /api/eval`).

## Prerequisites

Install the main backend deps, then the **training-only** packages:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

Training deps (`datasets`, `seqeval`, `evaluate`, `accelerate`) are grouped at the bottom of `requirements.txt` and are **not** required to run the FastAPI server.

## Quick local smoke test (CPU, ~2–5 min)

Verifies dataset loading, token alignment, Trainer loop, and metrics export on a tiny subset:

```bash
cd backend
python training/finetune_ner.py --smoke
python training/evaluate_baseline.py
```

Expected: script completes without errors; F1 will be **low** on 200 examples / 1 epoch — that is normal.

## Full fine-tune (Colab GPU, ~10 min)

For a real benchmark, use the Colab notebook on a free **T4 GPU**:

1. Open [`finetune_ner_colab.ipynb`](./finetune_ner_colab.ipynb) in Google Colab.
2. Run all cells (install → fine-tune 3 epochs → baseline comparison).
3. Optionally push weights to Hugging Face Hub (last cell).

Or from a GPU machine:

```bash
cd backend
python training/finetune_ner.py --epochs 3 --output_dir models/finetuned_ner
python training/evaluate_baseline.py
```

## Expected results

On the NCBI-Disease **test** split (entity-level, strict seqeval):

| Model | Typical F1 |
|-------|------------|
| Fine-tuned PubMedBERT (3 epochs, GPU) | **0.85–0.90** |
| Baseline `d4data/biomedical-ner-all` | **0.55–0.70** |

The fine-tuned model should clearly beat the general-purpose baseline because it is trained on the same label schema (`O`, `B-Disease`, `I-Disease`).

## Output artifacts

| Path | Contents |
|------|----------|
| `backend/models/finetuned_ner/` | Saved model + tokenizer (gitignored) |
| `backend/eval/finetune_metrics.json` | Fine-tune + baseline P/R/F1 |

### Metrics JSON shape

```json
{
  "model": "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract",
  "dataset": "ncbi/ncbi_disease",
  "epochs": 3,
  "precision": 0.87,
  "recall": 0.86,
  "f1": 0.86,
  "per_entity": { "Disease": { "...": "..." } },
  "baseline": {
    "model": "d4data/biomedical-ner-all",
    "f1": 0.62,
    "..."
  }
}
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `CHARTSCOPE_FINETUNE_BASE_MODEL` | `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract` | PubMedBERT checkpoint |
| `CHARTSCOPE_NER_MODEL` | `d4data/biomedical-ner-all` | Live app baseline (eval script) |

## CLI reference

### `finetune_ner.py`

```
python training/finetune_ner.py [--epochs 3] [--output_dir models/finetuned_ner]
                                [--smoke] [--push_to_hub --hub_model_id USER/repo]
```

### `evaluate_baseline.py`

```
python training/evaluate_baseline.py [--model d4data/biomedical-ner-all]
```

## Wiring into ChartScope (future)

Point the live NER pipeline at the fine-tuned weights:

```bash
export CHARTSCOPE_NER_MODEL=backend/models/finetuned_ner
```

Or push to Hub and set `CHARTSCOPE_NER_MODEL=your-username/chartscope-ncbi-ner`.
