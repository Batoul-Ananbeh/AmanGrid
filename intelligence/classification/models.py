"""Safe structured results produced by the classification engine."""

from dataclasses import dataclass
from enum import Enum


class ClassificationLevel(str, Enum):
    """The four sensitivity levels defined by the AmanGrid v1 contract."""

    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    RESTRICTED = "Restricted"


@dataclass(frozen=True)
class ClassificationEvidence:
    """A masked evidence item compatible with AnalysisDecision."""

    type: str
    excerpt: str

    def to_contract_item(self) -> dict[str, object]:
        """Return the safe evidence shape required by AnalysisDecision."""

        return {
            "type": self.type,
            "excerpt": self.excerpt,
            "masked": True,
        }


@dataclass(frozen=True)
class ClassificationResult:
    """Classification-owned output; risk and policy belong to later tasks."""

    level: ClassificationLevel
    confidence: int
    explanation: str
    scada_ot_relevant: bool
    energy_summary: str
    evidence: tuple[ClassificationEvidence, ...]
    uncertainty_reasons: tuple[str, ...]

    def to_contract_fields(self) -> dict[str, object]:
        """Return only the AnalysisDecision fields owned by AG-M-003."""

        return {
            "classification": {
                "level": self.level.value,
                "confidence": self.confidence,
                "explanation": self.explanation,
            },
            "energy_context": {
                "scada_ot_relevant": self.scada_ot_relevant,
                "summary": self.energy_summary,
            },
            "evidence": [
                item.to_contract_item()
                for item in self.evidence
            ],
        }
