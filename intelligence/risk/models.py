"""Safe, structured results produced by the AmanGrid risk engine."""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    """The four risk levels defined by the AmanGrid v1 contract."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RiskSeverity(str, Enum):
    """Explainable severity labels for individual risk factors."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RiskFactor:
    """One explainable contributor to the document risk score."""

    factor_id: str
    label: str
    severity: RiskSeverity
    explanation: str

    def to_contract_item(self) -> dict[str, str]:
        """Return the v1 AnalysisDecision risk-factor shape."""

        return {
            "factor_id": self.factor_id,
            "label": self.label,
            "severity": self.severity.value,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class RiskResult:
    """Risk-owned output; policy decisions belong to AG-M-005."""

    base_score: int
    final_score: int
    level: RiskLevel
    factors: tuple[RiskFactor, ...]
    triggered_overrides: tuple[str, ...]

    def to_contract_fields(self) -> dict[str, object]:
        """Return only the AnalysisDecision fields owned by AG-M-004."""

        return {
            "risk": {
                "base_score": self.base_score,
                "final_score": self.final_score,
                "level": self.level.value,
                "factors": [
                    factor.to_contract_item()
                    for factor in self.factors
                ],
                "triggered_overrides": list(self.triggered_overrides),
            }
        }