import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = REPOSITORY_ROOT / "contracts" / "v1"
EXAMPLE_ROOT = CONTRACT_ROOT / "examples"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


@pytest.fixture(scope="session")
def extracted_schema() -> dict:
    return load_json(CONTRACT_ROOT / "extracted_document.schema.json")


@pytest.fixture(scope="session")
def decision_schema() -> dict:
    return load_json(CONTRACT_ROOT / "analysis_decision.schema.json")


@pytest.fixture(scope="session")
def extracted_validator(extracted_schema: dict) -> Draft202012Validator:
    return Draft202012Validator(extracted_schema, format_checker=FormatChecker())


@pytest.fixture(scope="session")
def decision_validator(decision_schema: dict) -> Draft202012Validator:
    return Draft202012Validator(decision_schema, format_checker=FormatChecker())


@pytest.fixture(scope="session")
def fixture_pairs() -> list[tuple[dict, dict]]:
    pairs = []
    for prefix in ("public_low", "confidential_high", "restricted_critical"):
        pairs.append(
            (
                load_json(EXAMPLE_ROOT / f"{prefix}_input.json"),
                load_json(EXAMPLE_ROOT / f"{prefix}_output.json"),
            )
        )
    return pairs


@pytest.fixture
def valid_extracted(fixture_pairs: list[tuple[dict, dict]]) -> dict:
    return copy.deepcopy(fixture_pairs[0][0])


@pytest.fixture
def valid_decision(fixture_pairs: list[tuple[dict, dict]]) -> dict:
    return copy.deepcopy(fixture_pairs[0][1])
