"""Evaluate the ChartScope baseline NER on NCBI-Disease test split."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from training.ncbi_disease import (  # noqa: E402
    load_ncbi_disease,
    prepare_dataset_dict,
    spans_to_iob,
    tags_to_strings,
    tokens_to_text_and_offsets,
)

logger = logging.getLogger(__name__)

METRICS_PATH = BACKEND_ROOT / "eval" / "finetune_metrics.json"
DEFAULT_BASELINE_MODEL = "d4data/biomedical-ner-all"

# Labels from the general biomedical NER model mapped to NCBI "Disease".
BASELINE_DISEASE_RAW_LABELS = {
    "Disease_disorder",
    "Disease",
    "Specific_disease",
}


def _raw_label_name(label: str) -> str:
    if label == "O" or "-" not in label:
        return label
    return label.split("-", 1)[1]


def load_baseline_pipeline(model_id: str = DEFAULT_BASELINE_MODEL) -> Any:
    from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForTokenClassification.from_pretrained(model_id)
    return pipeline(
        "token-classification",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="first",
        device=-1,
    )


def predictions_to_disease_spans(predictions: list[dict[str, Any]]) -> list[dict[str, int]]:
    spans: list[dict[str, int]] = []
    for pred in predictions:
        raw = pred.get("entity_group") or pred.get("entity") or ""
        if _raw_label_name(raw) not in BASELINE_DISEASE_RAW_LABELS:
            continue
        spans.append({"start": int(pred["start"]), "end": int(pred["end"])})
    return spans


def evaluate_baseline(model_id: str = DEFAULT_BASELINE_MODEL) -> dict[str, Any]:
    from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

    raw_ds, dataset_source = load_ncbi_disease()
    ds = prepare_dataset_dict(raw_ds, source=dataset_source)
    test_ds = ds["test"]

    ner_pipe = load_baseline_pipeline(model_id)

    true_labels: list[list[str]] = []
    pred_labels: list[list[str]] = []

    for row in test_ds:
        tokens = row["tokens"]
        gold = tags_to_strings(row["ner_tags"])
        text, offsets = tokens_to_text_and_offsets(tokens)
        raw_preds = ner_pipe(text)
        disease_spans = predictions_to_disease_spans(raw_preds)
        pred = spans_to_iob(offsets, disease_spans)
        true_labels.append(gold)
        pred_labels.append(pred)

    report = classification_report(true_labels, pred_labels, output_dict=True)
    per_entity = {
        key: _json_safe(value)
        for key, value in report.items()
        if key not in {"micro avg", "macro avg", "weighted avg"}
    }

    return {
        "model": model_id,
        "dataset": dataset_source,
        "split": "test",
        "precision": float(precision_score(true_labels, pred_labels)),
        "recall": float(recall_score(true_labels, pred_labels)),
        "f1": float(f1_score(true_labels, pred_labels)),
        "per_entity": per_entity,
    }


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if hasattr(obj, "item") and callable(obj.item):
        try:
            return obj.item()
        except Exception:  # noqa: BLE001
            pass
    return obj


def append_baseline_metrics(baseline: dict[str, Any]) -> None:
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if METRICS_PATH.exists():
        existing = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    existing["baseline"] = _json_safe(baseline)
    METRICS_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    logger.info("Appended baseline metrics to %s", METRICS_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark ChartScope baseline NER on NCBI-Disease.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_BASELINE_MODEL,
        help="Baseline HuggingFace model id.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    logger.info("Evaluating baseline %s on NCBI-Disease test split…", args.model)
    baseline = evaluate_baseline(args.model)
    append_baseline_metrics(baseline)

    print("\n=== Baseline evaluation ===")
    print(f"Model:     {baseline['model']}")
    print(f"Dataset:   {baseline['dataset']}")
    print(f"Precision: {baseline['precision']:.4f}")
    print(f"Recall:    {baseline['recall']:.4f}")
    print(f"F1:        {baseline['f1']:.4f}")
    print(f"Metrics:   {METRICS_PATH}")


if __name__ == "__main__":
    main()
