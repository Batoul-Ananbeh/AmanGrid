import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from backend.app.api import routes
from backend.app.core.contracts import ContractFixtureError
from backend.app.main import app


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def test_health_endpoint_reports_service_identity() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "amangrid-api",
        "version": "0.1.0",
    }


def test_demo_analysis_matches_the_shared_v1_contract() -> None:
    response = client.get("/api/v1/demo/analysis")

    assert response.status_code == 200
    payload = response.json()
    schema = load_json(
        REPOSITORY_ROOT / "contracts" / "v1" / "analysis_decision.schema.json"
    )
    Draft202012Validator(schema).validate(payload)
    assert payload["contract_version"] == "1.0"
    assert all(
        recommendation["execution_mode"] in {"RECOMMENDED", "SIMULATED"}
        for recommendation in payload["policy"]["recommendations"]
    )


def test_demo_analysis_returns_a_safe_contract_error(monkeypatch) -> None:
    def fail_to_load_fixture() -> dict:
        raise ContractFixtureError("Internal fixture details must not cross the API.")

    monkeypatch.setattr(routes, "load_demo_analysis", fail_to_load_fixture)

    response = client.get("/api/v1/demo/analysis")

    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "code": "CONTRACT_VALIDATION_FAILED",
            "message": "The synthetic analysis response failed contract validation.",
        }
    }
    assert "Internal fixture details" not in response.text
