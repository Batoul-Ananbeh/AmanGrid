import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_ROOT = REPOSITORY_ROOT / "contracts" / "v1"
DEMO_ANALYSIS_PATH = CONTRACT_ROOT / "examples" / "restricted_critical_output.json"
DECISION_SCHEMA_PATH = CONTRACT_ROOT / "analysis_decision.schema.json"


class ContractFixtureError(RuntimeError):
    """Raised when a bundled synthetic fixture cannot cross the API boundary."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractFixtureError(f"Unable to load {path.name}.") from exc

    if not isinstance(value, dict):
        raise ContractFixtureError(f"{path.name} must contain a JSON object.")
    return value


@lru_cache(maxsize=1)
def _decision_validator() -> Draft202012Validator:
    schema = _load_json(DECISION_SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ContractFixtureError("The analysis decision schema is invalid.") from exc
    return Draft202012Validator(schema, format_checker=FormatChecker())


def load_demo_analysis() -> dict[str, Any]:
    payload = _load_json(DEMO_ANALYSIS_PATH)
    if payload.get("contract_version") != "1.0":
        raise ContractFixtureError("The demo uses an unsupported contract version.")

    try:
        _decision_validator().validate(payload)
    except ValidationError as exc:
        raise ContractFixtureError("The demo does not match AnalysisDecision v1.") from exc
    return payload
