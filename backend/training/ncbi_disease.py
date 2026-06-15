"""Load and normalize the public NCBI-Disease NER corpus."""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

LABEL_NAMES = ["O", "B-Disease", "I-Disease"]
LABEL2ID = {name: idx for idx, name in enumerate(LABEL_NAMES)}
ID2LABEL = {idx: name for name, idx in LABEL2ID.items()}

# (loader_fn, source_label)
_LOADER_ATTEMPTS: list[tuple[Callable[[], Any], str]] = []


def _register_loaders() -> list[tuple[Callable[[], Any], str]]:
    if _LOADER_ATTEMPTS:
        return _LOADER_ATTEMPTS

    from datasets import load_dataset

    def _try(name: str, fn: Callable[[], Any]) -> None:
        _LOADER_ATTEMPTS.append((fn, name))

    # Parquet export — required for datasets >= 4.x (script loading removed).
    _try(
        "ncbi/ncbi_disease@refs/convert/parquet",
        lambda: load_dataset("ncbi/ncbi_disease", revision="refs/convert/parquet"),
    )
    # Legacy script paths (datasets < 4.0).
    _try("ncbi_disease", lambda: load_dataset("ncbi_disease"))
    _try("ncbi/ncbi_disease", lambda: load_dataset("ncbi/ncbi_disease"))
    _try(
        "bigbio/ncbi_disease/ncbi_disease_source",
        lambda: load_dataset("bigbio/ncbi_disease", "ncbi_disease_source"),
    )
    _try(
        "bigbio/ncbi_disease/ncbi_disease_bigbio_kb_source",
        lambda: load_dataset("bigbio/ncbi_disease", "ncbi_disease_bigbio_kb_source"),
    )
    # Last resort — different corpus but public disease NER (not NCBI test split).
    _try(
        "tner/bc5cdr@refs/convert/parquet",
        lambda: load_dataset("tner/bc5cdr", revision="refs/convert/parquet"),
    )
    return _LOADER_ATTEMPTS


def _tag_to_str(tag: Any, feature: Any | None = None) -> str:
    if isinstance(tag, str):
        if tag in LABEL2ID:
            return tag
        if tag.isdigit():
            return ID2LABEL[int(tag)]
    if isinstance(tag, int):
        if feature is not None and hasattr(feature, "int2str"):
            return feature.int2str(tag)
        return ID2LABEL.get(tag, "O")
    return "O"


def _tags_to_strings(tags: list[Any], feature: Any | None = None) -> list[str]:
    return [_tag_to_str(t, feature) for t in tags]


def _bc5cdr_tags_to_ncbi(tags: list[Any], feature: Any | None = None) -> list[str]:
    """Map BC5CDR integer tags to NCBI IOB (Disease only; other entities -> O)."""
    out: list[str] = []
    for tag in tags:
        label = _tag_to_str(tag, feature) if feature else str(tag)
        if isinstance(tag, int) and feature is None:
            # BC5CDR parquet: 0=O, odd=B-*, even continuation — keep only Disease ids.
            # tner/bc5cdr uses unified tag ids; map B-Disease/I-Disease when present.
            label = ID2LABEL.get(tag, "O")
        if label in {"B-Disease", "I-Disease"}:
            out.append(label)
        elif label.startswith("B-") or label.startswith("I-"):
            out.append("O")
        else:
            out.append(label if label in LABEL2ID else "O")
    return out


def _bigbio_passage_to_iob(tokens: list[str], entities: list[dict[str, Any]]) -> list[str]:
    iob = ["O"] * len(tokens)
    char_offsets: list[tuple[int, int]] = []
    pos = 0
    for i, tok in enumerate(tokens):
        if i > 0:
            pos += 1
        start = pos
        pos += len(tok)
        char_offsets.append((start, pos))

    for ent in entities:
        ent_start = int(ent["start"])
        ent_end = int(ent["end"])
        covered: list[int] = []
        for idx, (s, e) in enumerate(char_offsets):
            if e <= ent_start or s >= ent_end:
                continue
            covered.append(idx)
        if not covered:
            continue
        iob[covered[0]] = "B-Disease"
        for idx in covered[1:]:
            iob[idx] = "I-Disease"
    return iob


def _normalize_row(
    row: dict[str, Any],
    tag_feature: Any | None = None,
    source: str = "",
) -> dict[str, Any]:
    if "tokens" in row and "ner_tags" in row:
        tokens = list(row["tokens"])
        tags = _tags_to_strings(list(row["ner_tags"]), tag_feature)
        return {"tokens": tokens, "ner_tags": tags}

    if "tokens" in row and "tags" in row:
        tokens = list(row["tokens"])
        tag_col = row["tags"]
        tag_feat = tag_feature
        if "bc5cdr" in source:
            tags = _bc5cdr_tags_to_ncbi(list(tag_col), tag_feat)
        else:
            tags = _tags_to_strings(list(tag_col), tag_feat)
        return {"tokens": tokens, "ner_tags": tags}

    if "tokens" in row and "entities" in row:
        tokens = list(row["tokens"])
        return {
            "tokens": tokens,
            "ner_tags": _bigbio_passage_to_iob(tokens, list(row["entities"])),
        }

    if "passages" in row:
        passage = row["passages"][0]
        tokens = list(passage["text"])
        entities = list(passage.get("entities", []))
        return {
            "tokens": tokens,
            "ner_tags": _bigbio_passage_to_iob(tokens, entities),
        }

    raise ValueError(f"Unrecognized NCBI-Disease row format: {list(row.keys())}")


def load_ncbi_disease() -> tuple[Any, str]:
    """Return (dataset_dict, source_name). Tries several public Hub paths."""
    last_error: Exception | None = None
    for loader, source in _register_loaders():
        try:
            ds = loader()
            logger.info("Loaded NCBI-Disease from %s", source)
            if "bc5cdr" in source:
                logger.warning(
                    "Using BC5CDR fallback — not the NCBI-Disease test split; "
                    "metrics are not comparable to published NCBI benchmarks.",
                )
            return ds, source
        except Exception as exc:  # noqa: BLE001 — try next candidate
            logger.debug("Failed to load %s: %s", source, exc)
            last_error = exc

    msg = "Could not load NCBI-Disease from any known Hub path."
    if last_error:
        raise RuntimeError(msg) from last_error
    raise RuntimeError(msg)


def prepare_dataset_dict(raw: Any, source: str = "") -> Any:
    """Map all splits to {tokens, ner_tags} with string IOB labels."""
    from datasets import DatasetDict

    tag_feature = None
    train_split = raw["train"] if isinstance(raw, DatasetDict) else raw
    if "ner_tags" in train_split.features:
        tag_feature = train_split.features["ner_tags"].feature
    elif "tags" in train_split.features:
        tag_feature = train_split.features["tags"].feature

    def _map_batch(batch: dict[str, list[Any]]) -> dict[str, list[Any]]:
        n = len(next(iter(batch.values())))
        tokens_out: list[list[str]] = []
        tags_out: list[list[str]] = []
        for i in range(n):
            row = {k: batch[k][i] for k in batch}
            norm = _normalize_row(row, tag_feature, source=source)
            tokens_out.append(norm["tokens"])
            tags_out.append([LABEL2ID[t] for t in norm["ner_tags"]])
        return {"tokens": tokens_out, "ner_tags": tags_out}

    if isinstance(raw, DatasetDict):
        return raw.map(_map_batch, batched=True, remove_columns=raw["train"].column_names)
    return raw.map(_map_batch, batched=True, remove_columns=raw.column_names)


def tags_to_strings(tags: list[int]) -> list[str]:
    return [ID2LABEL[t] for t in tags]


def tokens_to_text_and_offsets(tokens: list[str]) -> tuple[str, list[tuple[int, int]]]:
    """Rebuild note text and per-token char spans (space-separated)."""
    parts: list[str] = []
    offsets: list[tuple[int, int]] = []
    pos = 0
    for i, tok in enumerate(tokens):
        if i > 0:
            pos += 1
        start = pos
        parts.append(tok)
        pos += len(tok)
        offsets.append((start, pos))
    return " ".join(tokens), offsets


def spans_to_iob(
    offsets: list[tuple[int, int]],
    spans: list[dict[str, int]],
    entity: str = "Disease",
) -> list[str]:
    """Convert char spans to IOB tags aligned with token offsets."""
    iob = ["O"] * len(offsets)
    for span in sorted(spans, key=lambda s: s["start"]):
        covered: list[int] = []
        for idx, (s, e) in enumerate(offsets):
            if e <= span["start"] or s >= span["end"]:
                continue
            covered.append(idx)
        if not covered:
            continue
        iob[covered[0]] = f"B-{entity}"
        for idx in covered[1:]:
            iob[i] = f"I-{entity}"
    return iob
