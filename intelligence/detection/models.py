"""Data structures for safe, explainable detection results."""

from dataclasses import dataclass
from enum import Enum


class FindingType(str, Enum):
    """Stable finding names suitable for AnalysisDecision.sensitive_findings."""

    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    INTERNAL_IP = "INTERNAL_IP"
    CREDENTIAL = "CREDENTIAL"
    METER_ID = "METER_ID"
    CUSTOMER_ID = "CUSTOMER_ID"
    EQUIPMENT_ID = "EQUIPMENT_ID"
    SCADA_OT_INDICATOR = "SCADA_OT_INDICATOR"


@dataclass(frozen=True)
class DetectionFinding:
    """One finding type with an occurrence count and masked evidence only."""

    type: FindingType
    count: int
    evidence: tuple[str, ...]

    def to_contract_finding(self) -> dict[str, object]:
        """Return the contract-compatible subset for ``sensitive_findings``."""

        return {"type": self.type.value, "count": self.count}


@dataclass(frozen=True)
class DetectionResult:
    """Deterministic detection output; this module never logs source content."""

    findings: tuple[DetectionFinding, ...]

    def contract_findings(self) -> list[dict[str, object]]:
        """Return the list shape required by AnalysisDecision.sensitive_findings."""

        return [finding.to_contract_finding() for finding in self.findings]
