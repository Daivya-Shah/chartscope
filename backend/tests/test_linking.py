"""Tests for SapBERT + lexical terminology linking."""

from app.pipeline.linking import link_medication, link_problem


def test_link_type2_diabetes():
    result = link_problem("type 2 diabetes mellitus")
    assert result is not None
    assert result["icd10"].startswith("E11")
    assert result["score"] >= 0.5


def test_link_diabetic_ckd():
    result = link_problem("diabetic chronic kidney disease")
    assert result is not None
    code = result["icd10"]
    assert code in {"E11.22", "N18.3", "N18.32", "N18.30", "N18.9", "E11.29", "E11.21"} or code.startswith(
        ("E11", "N18")
    )
    assert result["score"] >= 0.5


def test_link_diabetic_polyneuropathy():
    result = link_problem("diabetic peripheral polyneuropathy")
    assert result is not None
    assert result["icd10"] in {"E11.42", "E11.40", "E10.42", "G62.9"} or result["icd10"].startswith("E11.4")
    assert result["score"] >= 0.5


def test_link_metformin_rxnorm():
    result = link_medication("metformin")
    assert result is not None
    assert result["rxnorm"] == "6809"
    assert "metformin" in result["rxnorm_name"].lower()
    assert result["score"] >= 0.75
