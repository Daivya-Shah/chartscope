"""Terminology linking via SapBERT semantic embeddings + lexical reranking."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
import numpy as np
import pandas as pd
import torch
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

TERM_DIR = Path(__file__).resolve().parents[1] / "data" / "terminology"
ICD10_CSV = TERM_DIR / "icd10_dictionary.csv"
MEDS_CSV = TERM_DIR / "medications_rxnorm.csv"
ICD10_EMB = TERM_DIR / "icd10_emb.npy"
ICD10_EMB_META = TERM_DIR / "icd10_emb.meta.json"

SAPBERT_MODEL = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"
MIN_NER_SCORE = 0.5
MIN_LINK_SCORE = 0.45
TOP_K = 10
SEMANTIC_WEIGHT = 0.55
LEXICAL_WEIGHT = 0.45

_sapbert_model: Any | None = None
_sapbert_tokenizer: Any | None = None
_icd10_codes: list[str] | None = None
_icd10_descriptions: list[str] | None = None
_icd10_embeddings: np.ndarray | None = None
_medications_df: pd.DataFrame | None = None


def _dictionary_hash() -> str:
    return hashlib.sha256(ICD10_CSV.read_bytes()).hexdigest()[:16]


def _get_sapbert() -> tuple[Any, Any]:
    global _sapbert_model, _sapbert_tokenizer
    if _sapbert_model is not None and _sapbert_tokenizer is not None:
        return _sapbert_model, _sapbert_tokenizer

    from transformers import AutoModel, AutoTokenizer

    logger.info("Loading SapBERT: %s", SAPBERT_MODEL)
    _sapbert_tokenizer = AutoTokenizer.from_pretrained(SAPBERT_MODEL)
    _sapbert_model = AutoModel.from_pretrained(SAPBERT_MODEL)
    _sapbert_model.eval()
    return _sapbert_model, _sapbert_tokenizer


def _embed_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
    if not texts:
        return np.zeros((0, 768), dtype=np.float32)

    model, tokenizer = _get_sapbert()
    all_embeddings: list[np.ndarray] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=64,
            return_tensors="pt",
        )
        with torch.no_grad():
            outputs = model(**inputs)
        token_embeddings = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
        summed = torch.sum(token_embeddings * attention_mask, dim=1)
        counts = torch.clamp(attention_mask.sum(dim=1), min=1e-9)
        mean_pooled = summed / counts
        vectors = mean_pooled.cpu().numpy().astype(np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / np.clip(norms, 1e-9, None)
        all_embeddings.append(vectors)

    return np.vstack(all_embeddings)


def _load_icd10_table() -> tuple[list[str], list[str]]:
    global _icd10_codes, _icd10_descriptions
    if _icd10_codes is not None and _icd10_descriptions is not None:
        return _icd10_codes, _icd10_descriptions

    df = pd.read_csv(ICD10_CSV)
    _icd10_codes = df["code"].astype(str).tolist()
    _icd10_descriptions = df["description"].astype(str).tolist()
    return _icd10_codes, _icd10_descriptions


def _load_icd10_embeddings() -> tuple[list[str], list[str], np.ndarray]:
    global _icd10_embeddings
    codes, descriptions = _load_icd10_table()
    current_hash = _dictionary_hash()

    if ICD10_EMB.exists() and ICD10_EMB_META.exists():
        meta = json.loads(ICD10_EMB_META.read_text(encoding="utf-8"))
        if meta.get("hash") == current_hash and meta.get("codes") == codes:
            _icd10_embeddings = np.load(ICD10_EMB)
            logger.info("Loaded cached ICD-10 embeddings (%d codes)", len(codes))
            return codes, descriptions, _icd10_embeddings

    logger.info("Building ICD-10 SapBERT embeddings for %d codes…", len(descriptions))
    _icd10_embeddings = _embed_texts(descriptions)
    np.save(ICD10_EMB, _icd10_embeddings)
    ICD10_EMB_META.write_text(
        json.dumps({"hash": current_hash, "codes": codes}, indent=2),
        encoding="utf-8",
    )
    logger.info("Cached ICD-10 embeddings to %s", ICD10_EMB)
    return codes, descriptions, _icd10_embeddings


def _load_medications() -> pd.DataFrame:
    global _medications_df
    if _medications_df is not None:
        return _medications_df
    _medications_df = pd.read_csv(MEDS_CSV)
    return _medications_df


def _normalize_mention(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip().lower())
    return cleaned


def _combined_score(semantic: float, lexical: float) -> float:
    return float(np.clip(SEMANTIC_WEIGHT * semantic + LEXICAL_WEIGHT * lexical, 0.0, 1.0))


def link_problem(text: str) -> dict[str, Any] | None:
    """Map a problem mention to the best ICD-10 code."""
    mention = _normalize_mention(text)
    if not mention:
        return None

    codes, descriptions, matrix = _load_icd10_embeddings()
    query = _embed_texts([mention])[0]
    semantic_scores = matrix @ query

    top_indices = np.argsort(semantic_scores)[-TOP_K:][::-1]
    best: dict[str, Any] | None = None
    best_score = -1.0

    for idx in top_indices:
        semantic = float(semantic_scores[idx])
        lexical = fuzz.token_sort_ratio(mention, descriptions[idx].lower()) / 100.0
        score = _combined_score(semantic, lexical)
        if score > best_score:
            best_score = score
            best = {
                "icd10": codes[idx],
                "icd10_desc": descriptions[idx],
                "score": score,
            }

    if best is None or best["score"] < MIN_LINK_SCORE:
        return None
    return best


def _rxnav_lookup(name: str) -> dict[str, str] | None:
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={quote(name)}&search=2"
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            payload = resp.json()
        ids = payload.get("idGroup", {}).get("rxnormId") or []
        if not ids:
            return None
        rxcui = str(ids[0])
        return {"rxnorm": rxcui, "rxnorm_name": name}
    except Exception as exc:  # noqa: BLE001 — offline fallback
        logger.debug("RxNav lookup failed for %r: %s", name, exc)
        return None


def link_medication(text: str, *, _allow_stem: bool = True) -> dict[str, Any] | None:
    """Map a medication mention to RxNorm via local dictionary + optional RxNav."""
    mention = _normalize_mention(text)
    if not mention:
        return None

    meds = _load_medications()
    names = meds["name"].astype(str).tolist()
    match = process.extractOne(
        mention,
        names,
        scorer=fuzz.token_sort_ratio,
    )
    if match and match[1] >= 75:
        row = meds.loc[meds["name"].astype(str).str.lower() == match[0].lower()].iloc[0]
        score = match[1] / 100.0
        return {
            "rxnorm": str(row["rxcui"]),
            "rxnorm_name": str(row["name"]),
            "score": score,
        }

    # Strip dose/frequency tokens and retry locally.
    stem = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|units|iu|bid|tid|qid|qhs|prn|daily)\b", "", mention)
    stem = re.sub(r"\s+", " ", stem).strip()
    if stem and stem != mention and _allow_stem:
        retry = link_medication(stem, _allow_stem=False)
        if retry:
            return retry

    remote = _rxnav_lookup(mention) or (_rxnav_lookup(stem) if stem else None)
    if remote:
        return {"rxnorm": remote["rxnorm"], "rxnorm_name": remote["rxnorm_name"], "score": 0.6}
    return None


def link_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate PROBLEM and MEDICATION entities with terminology links."""
    linked: list[dict[str, Any]] = []
    for ent in entities:
        updated = dict(ent)
        updated.setdefault("icd10", None)
        updated.setdefault("icd10_desc", None)
        updated.setdefault("rxnorm", None)
        updated.setdefault("rxnorm_name", None)
        updated.setdefault("link_score", None)

        ner_score = float(updated.get("score") or 0.0)
        if ner_score < MIN_NER_SCORE:
            linked.append(updated)
            continue

        label = updated.get("label")
        if label == "PROBLEM":
            result = link_problem(updated.get("text", ""))
            if result:
                updated["icd10"] = result["icd10"]
                updated["icd10_desc"] = result["icd10_desc"]
                updated["link_score"] = result["score"]
        elif label == "MEDICATION":
            result = link_medication(updated.get("text", ""))
            if result:
                updated["rxnorm"] = result["rxnorm"]
                updated["rxnorm_name"] = result["rxnorm_name"]
                updated["link_score"] = result["score"]

        linked.append(updated)
    return linked
