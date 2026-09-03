from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.core.config import get_settings
from backend.app.core.contracts import ContractFixtureError, load_demo_analysis


router = APIRouter(prefix="/api/v1")


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="amangrid-api",
        version=settings.app_version,
    )


@router.get("/demo/analysis", response_model=dict[str, Any], tags=["demo"])
def demo_analysis() -> dict[str, Any]:
    """Return a synthetic, schema-validated result for independent UI work."""

    try:
        return load_demo_analysis()
    except ContractFixtureError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONTRACT_VALIDATION_FAILED",
                "message": "The synthetic analysis response failed contract validation.",
            },
        ) from exc
