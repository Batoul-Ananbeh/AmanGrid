import copy

import pytest
from jsonschema import ValidationError


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"contract_version": "2.0"}),
        lambda value: value.update({"unexpected": True}),
        lambda value: value.pop("document_id"),
        lambda value: value.update({"file_metadata": {"file_name": "fabricated.txt"}}),
        lambda value: value.pop("text"),
        lambda value: value.update(
            {"extraction": {"status": "complete", "important_failure": True}}
        ),
    ],
)
def test_invalid_extracted_documents_are_rejected(
    extracted_validator, valid_extracted, mutation
):
    mutation(valid_extracted)
    with pytest.raises(ValidationError):
        extracted_validator.validate(valid_extracted)


def test_partial_extraction_without_usable_text_is_rejected(
    extracted_validator, valid_extracted
):
    valid_extracted.pop("text")
    valid_extracted["extraction"] = {
        "status": "partial",
        "important_failure": True,
        "issues": ["Important synthetic section was unreadable."],
    }
    with pytest.raises(ValidationError):
        extracted_validator.validate(valid_extracted)


@pytest.mark.parametrize("status", ["complete", "partial"])
def test_whitespace_only_text_is_rejected(extracted_validator, valid_extracted, status):
    valid_extracted["text"] = " \t\n "
    valid_extracted["extraction"] = {
        "status": status,
        "important_failure": False,
    }
    if status == "partial":
        valid_extracted["extraction"]["issues"] = ["Synthetic section was unreadable."]
    with pytest.raises(ValidationError):
        extracted_validator.validate(valid_extracted)


@pytest.mark.parametrize(
    ("input_kind", "mime_type"),
    [
        ("pdf", "application/msword"),
        ("word", "application/pdf"),
    ],
)
def test_mime_type_mismatch_is_rejected(
    extracted_validator, valid_extracted, input_kind, mime_type
):
    valid_extracted["input_kind"] = input_kind
    valid_extracted["file_metadata"] = {"mime_type": mime_type}
    with pytest.raises(ValidationError):
        extracted_validator.validate(valid_extracted)


def test_partial_extraction_without_issue_is_rejected(
    extracted_validator, valid_extracted
):
    valid_extracted["extraction"] = {
        "status": "partial",
        "important_failure": False,
    }
    with pytest.raises(ValidationError):
        extracted_validator.validate(valid_extracted)


def test_failed_extraction_with_text_is_rejected(extracted_validator, valid_extracted):
    valid_extracted["extraction"] = {
        "status": "failed",
        "important_failure": True,
        "failure_reason": "Synthetic failure.",
    }
    with pytest.raises(ValidationError):
        extracted_validator.validate(valid_extracted)


def test_failed_extraction_without_reason_is_rejected(
    extracted_validator, valid_extracted
):
    valid_extracted.pop("text")
    valid_extracted["extraction"] = {
        "status": "failed",
        "important_failure": True,
    }
    with pytest.raises(ValidationError):
        extracted_validator.validate(valid_extracted)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"contract_version": "0.9"}),
        lambda value: value.update({"unexpected": True}),
        lambda value: value["classification"].update({"confidence": 101}),
        lambda value: value["risk"].update({"final_score": -1}),
        lambda value: value["risk"].update({"level": "Severe"}),
        lambda value: value["policy"].update({"execution_mode": "EXECUTED"}),
        lambda value: value["evidence"][0].update({"masked": False}),
        lambda value: value["evidence"][0].update({"excerpt": "x" * 161}),
        lambda value: value["risk"].update({"final_score": 24, "level": "High"}),
        lambda value: value["risk"].update({"final_score": 25, "level": "Low"}),
        lambda value: value["risk"].update({"final_score": 74, "level": "Critical"}),
        lambda value: value["risk"].update({"final_score": 75, "level": "High"}),
        lambda value: value["policy"].pop("triggered_rule_ids"),
        lambda value: value["policy"].update({"triggered_rule_ids": ["invalid-rule"]}),
    ],
)
def test_invalid_analysis_decisions_are_rejected(
    decision_validator, valid_decision, mutation
):
    mutation(valid_decision)
    with pytest.raises(ValidationError):
        decision_validator.validate(valid_decision)


def test_review_required_without_reason_is_rejected(decision_validator, valid_decision):
    value = copy.deepcopy(valid_decision)
    value["policy"]["human_review_required"] = True
    value["policy"]["review_reasons"] = []
    with pytest.raises(ValidationError):
        decision_validator.validate(value)


def test_review_required_without_human_review_recommendation_is_rejected(
    decision_validator, valid_decision
):
    value = copy.deepcopy(valid_decision)
    value["policy"]["human_review_required"] = True
    value["policy"]["review_reasons"] = ["Synthetic review reason."]
    with pytest.raises(ValidationError):
        decision_validator.validate(value)


def test_non_review_decision_with_human_review_recommendation_is_rejected(
    decision_validator, valid_decision
):
    value = copy.deepcopy(valid_decision)
    value["policy"]["recommendations"] = ["HUMAN_REVIEW"]
    with pytest.raises(ValidationError):
        decision_validator.validate(value)


def test_allow_with_non_log_recommendation_is_rejected(decision_validator, valid_decision):
    value = copy.deepcopy(valid_decision)
    value["policy"]["recommendations"] = ["ALLOW", "WARN"]
    with pytest.raises(ValidationError):
        decision_validator.validate(value)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["risk"].update({"base_score": 80, "final_score": 80, "level": "Critical"}),
        lambda value: value["classification"].update({"confidence": 69}),
        lambda value: value["risk"].update({"triggered_overrides": ["DRAFT-OVERRIDE"]}),
    ],
)
def test_human_review_triggers_are_enforced(decision_validator, valid_decision, mutation):
    mutation(valid_decision)
    with pytest.raises(ValidationError):
        decision_validator.validate(valid_decision)
