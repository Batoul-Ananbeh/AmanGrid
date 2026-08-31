import copy

from jsonschema import Draft202012Validator


def test_schemas_are_valid_draft_2020_12(extracted_schema, decision_schema):
    assert extracted_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert decision_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(extracted_schema)
    Draft202012Validator.check_schema(decision_schema)


def test_exactly_three_fixture_pairs_exist(fixture_pairs):
    assert len(fixture_pairs) == 3


def test_all_extracted_document_fixtures_validate(extracted_validator, fixture_pairs):
    for extracted, _ in fixture_pairs:
        extracted_validator.validate(extracted)


def test_all_analysis_decision_fixtures_validate(decision_validator, fixture_pairs):
    for _, decision in fixture_pairs:
        decision_validator.validate(decision)


def test_supported_extraction_statuses_validate(extracted_validator, valid_extracted):
    complete = valid_extracted
    extracted_validator.validate(complete)

    partial = {**complete, "text": "Usable synthetic fragment."}
    partial["extraction"] = {
        "status": "partial",
        "important_failure": False,
        "issues": ["A synthetic section was unreadable."],
    }
    extracted_validator.validate(partial)

    failed = {
        key: value for key, value in complete.items() if key != "text"
    }
    failed["extraction"] = {
        "status": "failed",
        "important_failure": True,
        "failure_reason": "No usable synthetic text could be extracted.",
    }
    extracted_validator.validate(failed)


def test_matching_pdf_and_word_mime_types_validate(extracted_validator, valid_extracted):
    pdf = copy.deepcopy(valid_extracted)
    pdf["input_kind"] = "pdf"
    pdf["file_metadata"] = {"mime_type": "application/pdf"}
    extracted_validator.validate(pdf)

    word = copy.deepcopy(valid_extracted)
    word["input_kind"] = "word"
    word["file_metadata"] = {"mime_type": "application/msword"}
    extracted_validator.validate(word)
