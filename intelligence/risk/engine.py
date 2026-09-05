"""Deterministic, explainable risk scoring for AmanGrid."""

from __future__ import annotations

from collections.abc import Mapping

from intelligence.classification import ClassificationLevel, ClassificationResult
from intelligence.detection import DetectionResult, FindingType

from .models import RiskFactor, RiskLevel, RiskResult, RiskSeverity


CLASSIFICATION_SCORES = {
    ClassificationLevel.PUBLIC: 4,
    ClassificationLevel.INTERNAL: 14,
    ClassificationLevel.CONFIDENTIAL: 24,
    ClassificationLevel.RESTRICTED: 28,
}


def assess_risk(
    document: Mapping[str, object],
    classification: ClassificationResult,
    detection: DetectionResult,
) -> RiskResult:
    """Assess the current handling risk of a classified document.

    The engine uses only structured classification, detection, and supplied
    security context. Missing context is represented as ``unknown`` and is
    never treated as a confirmed security condition.
    """

    security_context = _security_context(document)
    finding_types = {finding.type for finding in detection.findings}

    sensitivity_score, sensitivity_factor = _data_sensitivity_factor(
        classification.level
    )
    operational_score, operational_factor = _operational_impact_factor(
        classification,
        finding_types,
    )
    exposure_score, exposure_factor = _exposure_level_factor(
        security_context.get("sharing_scope")
    )
    access_score, access_factor = _access_scope_factor(
        security_context.get("users_with_access")
    )
    storage_score, storage_factor = _storage_compliance_factor(
        security_context.get("storage_location")
    )
    protection_score, protection_factor = _protection_gap_factor(
        security_context.get("encryption_status")
    )

    base_score = min(
        100,
        sensitivity_score
        + operational_score
        + exposure_score
        + access_score
        + storage_score
        + protection_score,
    )

    final_score, triggered_overrides = _apply_overrides(
        base_score,
        classification,
        finding_types,
        security_context,
    )

    return RiskResult(
        base_score=base_score,
        final_score=final_score,
        level=_risk_level_for(final_score),
        factors=(
            sensitivity_factor,
            operational_factor,
            exposure_factor,
            access_factor,
            storage_factor,
            protection_factor,
        ),
        triggered_overrides=triggered_overrides,
    )


def _security_context(document: Mapping[str, object]) -> Mapping[str, object]:
    context = document.get("security_context")
    return context if isinstance(context, Mapping) else {}


def _data_sensitivity_factor(
    level: ClassificationLevel,
) -> tuple[int, RiskFactor]:
    score = CLASSIFICATION_SCORES[level]

    severity_by_level = {
        ClassificationLevel.PUBLIC: RiskSeverity.LOW,
        ClassificationLevel.INTERNAL: RiskSeverity.MEDIUM,
        ClassificationLevel.CONFIDENTIAL: RiskSeverity.HIGH,
        ClassificationLevel.RESTRICTED: RiskSeverity.CRITICAL,
    }

    return score, RiskFactor(
        factor_id="data_sensitivity",
        label="Data Sensitivity",
        severity=severity_by_level[level],
        explanation=(
            f"The document classification is {level.value}, which determines "
            "the baseline sensitivity risk."
        ),
    )


def _operational_impact_factor(
    classification: ClassificationResult,
    finding_types: set[FindingType],
) -> tuple[int, RiskFactor]:
    if classification.scada_ot_relevant:
        return 20, RiskFactor(
            factor_id="operational_impact",
            label="Operational Impact",
            severity=RiskSeverity.CRITICAL,
            explanation=(
                "Confirmed SCADA/OT context could affect critical energy "
                "operations if exposed."
            ),
        )

    if FindingType.CREDENTIAL in finding_types:
        return 16, RiskFactor(
            factor_id="operational_impact",
            label="Operational Impact",
            severity=RiskSeverity.HIGH,
            explanation=(
                "Credential-like access data could enable unauthorized access "
                "to operational systems."
            ),
        )

    if FindingType.INTERNAL_IP in finding_types:
        return 12, RiskFactor(
            factor_id="operational_impact",
            label="Operational Impact",
            severity=RiskSeverity.HIGH,
            explanation=(
                "Internal network information could increase the impact of "
                "unauthorized access."
            ),
        )

    if FindingType.EQUIPMENT_ID in finding_types:
        return 8, RiskFactor(
            factor_id="operational_impact",
            label="Operational Impact",
            severity=RiskSeverity.MEDIUM,
            explanation=(
                "Equipment identifiers provide operational context that "
                "requires controlled handling."
            ),
        )

    return 0, RiskFactor(
        factor_id="operational_impact",
        label="Operational Impact",
        severity=RiskSeverity.NONE,
        explanation="No confirmed operational-control impact was detected.",
    )


def _exposure_level_factor(value: object) -> tuple[int, RiskFactor]:
    mapping = {
        "private": (
            0,
            RiskSeverity.NONE,
            "The supplied context indicates private sharing only.",
        ),
        "restricted_group": (
            3,
            RiskSeverity.LOW,
            "The supplied context limits sharing to a restricted group.",
        ),
        "department_wide": (
            7,
            RiskSeverity.MEDIUM,
            "The supplied context allows sharing across a department.",
        ),
        "organization_wide": (
            10,
            RiskSeverity.HIGH,
            "The supplied context allows organization-wide sharing.",
        ),
        "external": (
            15,
            RiskSeverity.CRITICAL,
            "The supplied context indicates external sharing.",
        ),
    }

    if value not in mapping:
        return 0, RiskFactor(
            factor_id="exposure_level",
            label="Exposure Level",
            severity=RiskSeverity.UNKNOWN,
            explanation="Sharing scope was not supplied or is unknown.",
        )

    score, severity, explanation = mapping[value]
    return score, RiskFactor(
        factor_id="exposure_level",
        label="Exposure Level",
        severity=severity,
        explanation=explanation,
    )


def _access_scope_factor(value: object) -> tuple[int, RiskFactor]:
    if not isinstance(value, int) or isinstance(value, bool):
        return 0, RiskFactor(
            factor_id="access_scope",
            label="Access Scope",
            severity=RiskSeverity.UNKNOWN,
            explanation="The number of users with access was not supplied.",
        )

    if value <= 2:
        score, severity = 0, RiskSeverity.NONE
    elif value <= 5:
        score, severity = 2, RiskSeverity.LOW
    elif value <= 10:
        score, severity = 5, RiskSeverity.MEDIUM
    elif value <= 25:
        score, severity = 8, RiskSeverity.HIGH
    else:
        score, severity = 10, RiskSeverity.CRITICAL

    return score, RiskFactor(
        factor_id="access_scope",
        label="Access Scope",
        severity=severity,
        explanation=f"The supplied context reports {value} users with access.",
    )


def _storage_compliance_factor(value: object) -> tuple[int, RiskFactor]:
    mapping = {
        "approved_repository": (
            0,
            RiskSeverity.NONE,
            "The supplied context identifies an approved repository.",
        ),
        "local_device": (
            5,
            RiskSeverity.MEDIUM,
            "The supplied context identifies local-device storage.",
        ),
        "unapproved_repository": (
            8,
            RiskSeverity.HIGH,
            "The supplied context identifies an unapproved repository.",
        ),
        "personal_cloud": (
            10,
            RiskSeverity.CRITICAL,
            "Personal cloud storage is not an approved repository for "
            "sensitive energy data.",
        ),
    }

    if value not in mapping:
        return 0, RiskFactor(
            factor_id="storage_compliance",
            label="Storage Compliance",
            severity=RiskSeverity.UNKNOWN,
            explanation="Storage location was not supplied or is unknown.",
        )

    score, severity, explanation = mapping[value]
    return score, RiskFactor(
        factor_id="storage_compliance",
        label="Storage Compliance",
        severity=severity,
        explanation=explanation,
    )


def _protection_gap_factor(value: object) -> tuple[int, RiskFactor]:
    if value == "encrypted":
        return 0, RiskFactor(
            factor_id="protection_gap",
            label="Protection Gap",
            severity=RiskSeverity.NONE,
            explanation="The supplied context reports that the document is encrypted.",
        )

    if value == "not_encrypted":
        return 7, RiskFactor(
            factor_id="protection_gap",
            label="Protection Gap",
            severity=RiskSeverity.CRITICAL,
            explanation=(
                "The supplied context reports that the document is not encrypted."
            ),
        )

    return 0, RiskFactor(
        factor_id="protection_gap",
        label="Protection Gap",
        severity=RiskSeverity.UNKNOWN,
        explanation="Encryption status was not supplied or is unknown.",
    )


def _apply_overrides(
    base_score: int,
    classification: ClassificationResult,
    finding_types: set[FindingType],
    security_context: Mapping[str, object],
) -> tuple[int, tuple[str, ...]]:
    final_score = base_score
    triggered: list[str] = []

    if (
        classification.scada_ot_relevant
        and FindingType.CREDENTIAL in finding_types
    ):
        triggered.append("DRAFT-SCADA-CREDENTIAL")
        final_score = max(final_score, 88)

    if (
        classification.level is ClassificationLevel.RESTRICTED
        and security_context.get("sharing_scope") == "external"
    ):
        triggered.append("DRAFT-RESTRICTED-EXTERNAL")
        final_score = max(final_score, 92)

    return min(100, final_score), tuple(triggered)


def _risk_level_for(score: int) -> RiskLevel:
    if score <= 24:
        return RiskLevel.LOW
    if score <= 49:
        return RiskLevel.MEDIUM
    if score <= 74:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL