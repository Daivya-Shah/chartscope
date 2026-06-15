"""Fine-tune PubMedBERT for token-classification NER on NCBI-Disease."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from training.ncbi_disease import (  # noqa: E402
    ID2LABEL,
    LABEL2ID,
    load_ncbi_disease,
    prepare_dataset_dict,
    tags_to_strings,
)

logger = logging.getLogger(__name__)

DEFAULT_BASE_MODEL = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract"
FALLBACK_BASE_MODEL = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "models" / "finetuned_ner"
METRICS_PATH = BACKEND_ROOT / "eval" / "finetune_metrics.json"


def resolve_base_model() -> str:
    model_id = os.getenv("CHARTSCOPE_FINETUNE_BASE_MODEL", DEFAULT_BASE_MODEL)
    from transformers import AutoConfig

    try:
        AutoConfig.from_pretrained(model_id)
        return model_id
    except Exception as exc:  # noqa: BLE001
        logger.warning("Base model %s unavailable (%s); trying fallback.", model_id, exc)
        AutoConfig.from_pretrained(FALLBACK_BASE_MODEL)
        return FALLBACK_BASE_MODEL


def build_compute_metrics(label_names: list[str]):
    from seqeval.metrics import f1_score, precision_score, recall_score

    def compute_metrics(eval_pred: tuple[np.ndarray, np.ndarray]) -> dict[str, float]:
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=2)

        true_labels: list[list[str]] = []
        pred_labels: list[list[str]] = []

        for pred_row, label_row in zip(predictions, labels):
            true_seq: list[str] = []
            pred_seq: list[str] = []
            for pred_id, label_id in zip(pred_row, label_row):
                if label_id == -100:
                    continue
                true_seq.append(label_names[label_id])
                pred_seq.append(label_names[pred_id])
            true_labels.append(true_seq)
            pred_labels.append(pred_seq)

        return {
            "precision": float(precision_score(true_labels, pred_labels)),
            "recall": float(recall_score(true_labels, pred_labels)),
            "f1": float(f1_score(true_labels, pred_labels)),
        }

    return compute_metrics


def _json_safe(obj: Any) -> Any:
    """Recursively convert numpy scalars for JSON export."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


def entity_level_report(
    true_labels: list[list[str]],
    pred_labels: list[list[str]],
) -> dict[str, Any]:
    from seqeval.metrics import classification_report

    report = classification_report(true_labels, pred_labels, output_dict=True)
    per_entity = {
        key: _json_safe(value)
        for key, value in report.items()
        if key not in {"micro avg", "macro avg", "weighted avg"}
    }
    return {
        "precision": float(report["micro avg"]["precision"]),
        "recall": float(report["micro avg"]["recall"]),
        "f1": float(report["micro avg"]["f1-score"]),
        "per_entity": per_entity,
    }


def collect_predictions(
    trainer: Any,
    dataset: Any,
    label_names: list[str],
) -> tuple[list[list[str]], list[list[str]]]:
    predictions = trainer.predict(dataset)
    logits = predictions.predictions
    labels = predictions.label_ids
    pred_ids = np.argmax(logits, axis=2)

    true_labels: list[list[str]] = []
    pred_labels: list[list[str]] = []
    for pred_row, label_row in zip(pred_ids, labels):
        true_seq: list[str] = []
        pred_seq: list[str] = []
        for pred_id, label_id in zip(pred_row, label_row):
            if label_id == -100:
                continue
            true_seq.append(label_names[label_id])
            pred_seq.append(label_names[pred_id])
        true_labels.append(true_seq)
        pred_labels.append(pred_seq)
    return true_labels, pred_labels


def write_metrics(payload: dict[str, Any]) -> None:
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if METRICS_PATH.exists():
        existing = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    existing.update(_json_safe(payload))
    METRICS_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    logger.info("Wrote metrics to %s", METRICS_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune PubMedBERT on NCBI-Disease NER.")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs (default: 3).")
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for saved model + tokenizer.",
    )
    parser.add_argument(
        "--push_to_hub",
        action="store_true",
        help="Push fine-tuned weights to the Hugging Face Hub.",
    )
    parser.add_argument(
        "--hub_model_id",
        type=str,
        default=None,
        help="Hub repo id (required when --push_to_hub is set).",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick CPU sanity run: 200 train / 50 eval examples, 1 epoch.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    if args.push_to_hub and not args.hub_model_id:
        raise SystemExit("--hub_model_id is required when --push_to_hub is set.")

    from transformers import (
        AutoModelForTokenClassification,
        AutoTokenizer,
        DataCollatorForTokenClassification,
        Trainer,
        TrainingArguments,
    )

    base_model = resolve_base_model()
    epochs = 1 if args.smoke else args.epochs
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_ds, dataset_source = load_ncbi_disease()
    ds = prepare_dataset_dict(raw_ds, source=dataset_source)

    if args.smoke:
        ds["train"] = ds["train"].select(range(min(200, len(ds["train"]))))
        eval_split = "validation" if "validation" in ds else "test"
        ds[eval_split] = ds[eval_split].select(range(min(50, len(ds[eval_split]))))
    else:
        eval_split = "validation" if "validation" in ds else "test"

    label_names = list(ID2LABEL.values())
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    def tokenize_and_align_labels(examples: dict[str, list[Any]]) -> dict[str, Any]:
        tokenized = tokenizer(
            examples["tokens"],
            truncation=True,
            is_split_into_words=True,
            max_length=512,
        )
        all_labels: list[list[int]] = []
        for i, tags in enumerate(examples["ner_tags"]):
            word_ids = tokenized.word_ids(batch_index=i)
            label_ids: list[int] = []
            previous_word_idx: int | None = None
            for word_idx in word_ids:
                if word_idx is None:
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:
                    label_ids.append(int(tags[word_idx]))
                else:
                    label_ids.append(-100)
                previous_word_idx = word_idx
            all_labels.append(label_ids)
        tokenized["labels"] = all_labels
        return tokenized

    tokenized = ds.map(
        tokenize_and_align_labels,
        batched=True,
        remove_columns=ds["train"].column_names,
    )

    model = AutoModelForTokenClassification.from_pretrained(
        base_model,
        num_labels=len(label_names),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    training_args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=8 if not args.smoke else 4,
        per_device_eval_batch_size=8 if not args.smoke else 4,
        learning_rate=5e-5,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=10 if args.smoke else 50,
        load_best_model_at_end=not args.smoke,
        metric_for_best_model="f1",
        greater_is_better=True,
        report_to="none",
        push_to_hub=args.push_to_hub,
        hub_model_id=args.hub_model_id,
    )

    data_collator = DataCollatorForTokenClassification(tokenizer)
    compute_metrics = build_compute_metrics(label_names)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized[eval_split],
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    logger.info(
        "Starting fine-tune — model=%s dataset=%s smoke=%s epochs=%d",
        base_model,
        dataset_source,
        args.smoke,
        epochs,
    )
    trainer.train()

    test_split = "test" if "test" in tokenized else eval_split
    true_labels, pred_labels = collect_predictions(trainer, tokenized[test_split], label_names)
    metrics = entity_level_report(true_labels, pred_labels)

    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    payload = {
        "model": base_model,
        "output_dir": str(output_dir),
        "dataset": dataset_source,
        "epochs": epochs,
        "smoke": args.smoke,
        **metrics,
    }
    write_metrics(payload)

    print("\n=== Fine-tune complete ===")
    print(f"Model:     {base_model}")
    print(f"Dataset:   {dataset_source}")
    print(f"Epochs:    {epochs}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1:        {metrics['f1']:.4f}")
    print(f"Saved to:  {output_dir}")
    print(f"Metrics:   {METRICS_PATH}")


if __name__ == "__main__":
    main()
