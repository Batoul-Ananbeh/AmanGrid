"""Deterministic, conservative document classification for AmanGrid."""

from __future__ import annotations

import re
from collections.abc import Mapping

from intelligence.detection import DetectionFinding, DetectionResult, FindingType

from .models import (
    ClassificationEvidence,
    ClassificationLevel,
    ClassificationResult,
)


PUBLIC_CONTENT_PATTERN = re.compile(
    r"\b(?:public\s+(?:notice|report|announcement)|published|press\s+release|"
    r"community\s+energy-awareness|energy-awareness\s+(?:event|campaign))\b",
    re.IGNORECASE,
)

INTERNAL_CONTENT_PATTERN = re.compile(
    r"\b(?:internal\s+(?:procedure|report|instruction)|work\s+instruction|"
    r"maintenance\s+(?:procedure|schedule)|meeting\s+(?:agenda|schedule))\b",
    re.IGNORECASE,
)

STRONG_OT_PATTERN = re.compile(
    r"\b(?:SCADA|OT|PLC|RTU|HMI|DCS|substation)\b",
    re.IGNORECASE,
)

RESTRICTED_TYPES = frozenset(
    {
        FindingType.CREDENTIAL,
        FindingType.INTERNAL_IP,
    }
)

CONFIDENTIAL_TYPES = frozenset(
    {
        FindingType.EMAIL_ADDRESS,
        FindingType.METER_ID,
        FindingType.CUSTOMER_ID,
        FindingType.EQUIPMENT_ID,
    }
)


def classify_document(
    document: Mapping[str, object],
    detection: DetectionResult,
) -> ClassificationResult:
    """Classify usable extracted text using deterministic safety-first rules."""

    text = _usable_text(document)
    finding_map = {
        finding.type: finding
        for finding in detection.findings
    }

    strong_ot = bool(STRONG_OT_PATTERN.search(text))
    restricted = bool(RESTRICTED_TYPES & finding_map.keys()) or strong_ot
    confidential = bool(CONFIDENTIAL_TYPES & finding_map.keys())
    partial_failure = _has_important_partial_failure(document)

    if restricted:
        result = _restricted_result(finding_map, strong_ot)
    elif confidential:
        result = _confidential_result(finding_map)
    elif PUBLIC_CONTENT_PATTERN.search(text):
        result = _public_result()
    elif INTERNAL_CONTENT_PATTERN.search(text):
        result = _internal_result(confident=True)
    else:
        result = _internal_result(confident=False)

    if not partial_failure:
        return result

    return ClassificationResult(
        level=result.level,
        confidence=max(0, result.confidence - 20),
        explanation=result.explanation,
        scada_ot_relevant=result.scada_ot_relevant,
        energy_summary=result.energy_summary,
        evidence=result.evidence,
        uncertainty_reasons=(
            *result.uncertainty_reasons,
            "Important partial extraction reduces classification confidence.",
        ),
    )


def _usable_text(document: Mapping[str, object]) -> str:
    extraction = document.get("extraction")

    if not isinstance(extraction, Mapping):
        raise ValueError("document extraction state is required")

    if extraction.get("status") == "failed":
        raise ValueError("failed extraction cannot be classified")

    text = document.get("text")

    if not isinstance(text, str) or not text.strip():
        raise ValueError("usable document text is required")

    return text


def _has_important_partial_failure(
    document: Mapping[str, object],
) -> bool:
    extraction = document["extraction"]
    assert isinstance(extraction, Mapping)

    return (
        extraction.get("status") == "partial"
        and extraction.get("important_failure") is True
    )


def _restricted_result(
    finding_map: Mapping[FindingType, DetectionFinding],
    strong_ot: bool,
) -> ClassificationResult:
    finding_types = set(finding_map)

    if (
        FindingType.CREDENTIAL in finding_types
        and (strong_ot or FindingType.INTERNAL_IP in finding_types)
    ):
        confidence = 97
        explanation = (
            "Restricted access data is combined with critical operational "
            "or internal network context."
        )
    elif strong_ot:
        confidence = 92
        explanation = "The document contains critical SCADA/OT operational context."
    elif FindingType.CREDENTIAL in finding_types:
        confidence = 94
        explanation = "The document contains credential-like access data."
    else:
        confidence = 88
        explanation = (
            "The document contains internal network information that "
            "requires restricted handling."
        )

    return ClassificationResult(
        level=ClassificationLevel.RESTRICTED,
        confidence=confidence,
        explanation=explanation,
        scada_ot_relevant=strong_ot,
        energy_summary=(
            "Critical SCADA/OT operational context was detected."
            if strong_ot
            else "No confirmed SCADA/OT control context was detected."
        ),
        evidence=_evidence_for(
            finding_map,
            RESTRICTED_TYPES | {FindingType.SCADA_OT_INDICATOR},
        ),
        uncertainty_reasons=(),
    )


def _confidential_result(
    finding_map: Mapping[FindingType, DetectionFinding],
) -> ClassificationResult:
    relevant_types = CONFIDENTIAL_TYPES & set(finding_map)

    return ClassificationResult(
        level=ClassificationLevel.CONFIDENTIAL,
        confidence=92 if len(relevant_types) > 1 else 86,
        explanation=(
            "The document contains customer, personal, or operational "
            "identifiers requiring confidential handling."
        ),
        scada_ot_relevant=False,
        energy_summary="No confirmed SCADA/OT control context was detected.",
        evidence=_evidence_for(finding_map, CONFIDENTIAL_TYPES),
        uncertainty_reasons=(),
    )


def _public_result() -> ClassificationResult:
    return ClassificationResult(
        level=ClassificationLevel.PUBLIC,
        confidence=85,
        explanation=(
            "The document contains explicit public-distribution language "
            "and no sensitive findings."
        ),
        scada_ot_relevant=False,
        energy_summary=(
            "General public energy information without operational control context."
        ),
        evidence=(),
        uncertainty_reasons=(),
    )


def _internal_result(*, confident: bool) -> ClassificationResult:
    return ClassificationResult(
        level=ClassificationLevel.INTERNAL,
        confidence=74 if confident else 55,
        explanation=(
            "The document contains internal operational or administrative "
            "language without detected sensitive data."
            if confident
            else "No reliable public-distribution evidence or sensitive finding "
            "was detected; internal handling is the safe default."
        ),
        scada_ot_relevant=False,
        energy_summary="No confirmed SCADA/OT control context was detected.",
        evidence=(),
        uncertainty_reasons=(
            ()
            if confident
            else ("Insufficient context to classify the content as Public.",)
        ),
    )


def _evidence_for(
    finding_map: Mapping[FindingType, DetectionFinding],
    allowed_types: frozenset[FindingType] | set[FindingType],
) -> tuple[ClassificationEvidence, ...]:
    """Reuse only already-masked detector evidence."""

    evidence: list[ClassificationEvidence] = []

    for finding_type, finding in finding_map.items():
        if finding_type not in allowed_types:
            continue

        for excerpt in finding.evidence:
            evidence.append(
                ClassificationEvidence(
                    type=finding_type.value,
                    excerpt=excerpt,
                )
            )

    return tuple(evidence[:100])
