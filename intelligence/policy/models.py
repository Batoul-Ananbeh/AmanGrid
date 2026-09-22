"""Safe, structured results produced by the AmanGrid policy engine."""

from dataclasses import dataclass
from enum import Enum


class PolicyAction(str, Enum):
    """Actions permitted by the AnalysisDecision v1 policy contract."""

    ALLOW = "ALLOW"
    LOG = "LOG"
    WARN = "WARN"
    REQUIRE_JUSTIFICATION = "REQUIRE_JUSTIFICATION"
    RESTRICT_ACCESS = "RESTRICT_ACCESS"
    BLOCK = "BLOCK"
    ENCRYPT = "ENCRYPT"
    QUARANTINE = "QUARANTINE"
    ALERT = "ALERT"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class ExecutionMode(str, Enum):
    """MVP-only advisory execution modes."""

    RECOMMENDED = "RECOMMENDED"
    SIMULATED = "SIMULATED"


@dataclass(frozen=True)
class PolicyRecommendation:
    """One explainable policy recommendation."""

    action: PolicyAction
    execution_mode: ExecutionMode
    is_primary: bool
    reason: str

    def to_contract_item(self) -> dict[str, object]:
        """Return the v1 AnalysisDecision recommendation shape."""

        return {
            "action": self.action.value,
            "execution_mode": self.execution_mode.value,
            "is_primary": self.is_primary,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class PolicyResult:
    """Policy-owned output compatible with AnalysisDecision v1."""

    policy_version: str
    recommendations: tuple[PolicyRecommendation, ...]
    human_review_required: bool
    review_reasons: tuple[str, ...]
    triggered_rule_ids: tuple[str, ...]

    def to_contract_fields(self) -> dict[str, object]:
        """Return only the AnalysisDecision fields owned by AG-M-005."""

        return {
            "policy": {
                "recommendations": [
                    item.to_contract_item()
                    for item in self.recommendations
                ],
                "human_review_required": self.human_review_required,
                "review_reasons": list(self.review_reasons),
                "triggered_rule_ids": list(self.triggered_rule_ids),
            }
        }
