"""Tests for NCBI-Disease IOB conversion helpers."""

from training.ncbi_disease import spans_to_iob, tokens_to_text_and_offsets


def test_spans_to_iob_multi_token_entity():
    tokens = ["Patient", "has", "breast", "cancer", "today"]
    _, offsets = tokens_to_text_and_offsets(tokens)
    # "breast cancer" spans tokens 2–3
    breast_start = offsets[2][0]
    cancer_end = offsets[3][1]
    spans = [{"start": breast_start, "end": cancer_end}]

    iob = spans_to_iob(offsets, spans)

    assert iob == ["O", "O", "B-Disease", "I-Disease", "O"]


def test_spans_to_iob_single_token_entity():
    tokens = ["No", "fever", "noted"]
    _, offsets = tokens_to_text_and_offsets(tokens)
    spans = [{"start": offsets[1][0], "end": offsets[1][1]}]

    iob = spans_to_iob(offsets, spans)

    assert iob == ["O", "B-Disease", "O"]
