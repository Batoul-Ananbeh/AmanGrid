import copy
from pathlib import Path

import pytest


EXPECTED_FACTOR_IDS = {
    "data_sensitivity",
    "operational_impact",
    "exposure_level",
    "access_scope",
    "storage_compliance",
    "protection_gap",
}

RISK_RANGES = {
    "Low": range(0, 25),
    "Medium": range(25, 50),
    "High": range(50, 75),
    "Critical": range(75, 101),
}


def assert_decision_semantics(decision: dict) -> None:
    risk = decision["risk"]
    assert risk["final_score"] >= risk["base_score"], (
        "Final risk score must not be below base risk score"
    )
    factor_ids = [factor["factor_id"] for factor in risk["factors"]]
    assert len(factor_ids) == len(set(factor_ids)), "Risk factor IDs must be unique"


def assert_pair_consistent(extracted: dict, decision: dict) -> None:
    if extracted["extraction"]["status"] == "failed":
        raise AssertionError("Failed extraction must not produce AnalysisDecision")

    assert extracted["contract_version"] == decision["contract_version"] == "1.0"
    assert extracted["document_id"] == decision["document_id"]
    assert_decision_semantics(decision)

    extraction = extracted["extraction"]
    if extraction["status"] == "partial" and extraction["important_failure"]:
        assert decision["policy"]["human_review_required"] is True
        assert decision["policy"]["review_reasons"]


def test_fixture_files_are_exactly_three_pairs():
    example_root = Path(__file__).resolve().parents[2] / "contracts" / "v1" / "examples"
    json_files = sorted(example_root.glob("*.json"))
    assert len(json_files) == 6
    assert {path.stem.removesuffix("_input").removesuffix("_output") for path in json_files} == {
        "public_low",
        "confidential_high",
        "restricted_critical",
    }


def test_fixture_pairs_share_version_and_document_identity(fixture_pairs):
    for extracted, decision in fixture_pairs:
        assert_pair_consistent(extracted, decision)


def test_failed_extraction_cannot_have_a_decision(fixture_pairs):
    failed = copy.deepcopy(fixture_pairs[0][0])
    failed.pop("text")
    failed["extraction"] = {
        "status": "failed",
        "important_failure": True,
        "failure_reason": "No usable synthetic text.",
    }
    with pytest.raises(AssertionError, match="must not produce"):
        assert_pair_consistent(failed, fixture_pairs[0][1])


def test_fixture_classification_and_risk_coverage(fixture_pairs):
    observed = {
        (decision["classification"]["level"], decision["risk"]["level"])
        for _, decision in fixture_pairs
    }
    assert observed == {
        ("Public", "Low"),
        ("Confidential", "High"),
        ("Restricted", "Critical"),
    }


def test_fixture_risk_levels_match_final_score_ranges(fixture_pairs):
    for _, decision in fixture_pairs:
        risk = decision["risk"]
        assert risk["final_score"] in RISK_RANGES[risk["level"]]


def test_test_layer_semantics_reject_invalid_score_order(fixture_pairs):
    decision = copy.deepcopy(fixture_pairs[0][1])
    decision["risk"]["base_score"] = 9
    decision["risk"]["final_score"] = 8
    with pytest.raises(AssertionError, match="must not be below"):
        assert_decision_semantics(decision)


def test_test_layer_semantics_reject_duplicate_factor_ids(fixture_pairs):
    decision = copy.deepcopy(fixture_pairs[0][1])
    decision["risk"]["factors"][1]["factor_id"] = "data_sensitivity"
    with pytest.raises(AssertionError, match="must be unique"):
        assert_decision_semantics(decision)


def test_each_fixture_uses_the_six_current_risk_factors(fixture_pairs):
    for _, decision in fixture_pairs:
        factors = decision["risk"]["factors"]
        assert len(factors) == 6
        assert {factor["factor_id"] for factor in factors} == EXPECTED_FACTOR_IDS


def test_evidence_is_masked_and_bounded(fixture_pairs):
    for _, decision in fixture_pairs:
        for evidence in decision["evidence"]:
            assert evidence["masked"] is True
            assert 1 <= len(evidence["excerpt"]) <= 160
            assert "[" in evidence["excerpt"] and "]" in evidence["excerpt"]


def test_manual_text_has_no_fabricated_file_metadata(fixture_pairs):
    manual_inputs = [value for value, _ in fixture_pairs if value["input_kind"] == "manual_text"]
    assert manual_inputs
    assert all("file_metadata" not in value for value in manual_inputs)


def test_fixture_triggered_rule_ids_are_stable_and_scenario_specific(fixture_pairs):
    observed = {
        decision["document_id"]: decision["policy"]["triggered_rule_ids"]
        for _, decision in fixture_pairs
    }
    assert observed == {
        "doc-public-001": ["PUBLIC-01"],
        "doc-confidential-001": ["PRIVACY-02"],
        "doc-restricted-001": ["ENERGY-OT-04"],
    }
