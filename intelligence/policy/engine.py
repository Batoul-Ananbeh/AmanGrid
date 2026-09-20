"""Deterministic, explainable policy recommendations for AmanGrid."""

from intelligence.classification import ClassificationLevel, ClassificationResult
from intelligence.risk import RiskLevel, RiskResult

from .models import (
    ExecutionMode,
    PolicyAction,
    PolicyRecommendation,
    PolicyResult,
)


POLICY_VERSION = "1.0"

SIMULATED_ACTIONS = frozenset(
    {
        PolicyAction.BLOCK,
        PolicyAction.QUARANTINE,
    }
)

RULE_ACTIONS = {
    (ClassificationLevel.PUBLIC, RiskLevel.LOW): (
        "POL-V1-PUBLIC-LOW",
        (PolicyAction.ALLOW, PolicyAction.LOG),
    ),
    (ClassificationLevel.PUBLIC, RiskLevel.MEDIUM): (
        "POL-V1-PUBLIC-MEDIUM",
        (PolicyAction.WARN,),
    ),
    (ClassificationLevel.PUBLIC, RiskLevel.HIGH): (
        "POL-V1-PUBLIC-HIGH",
        (PolicyAction.WARN,),
    ),
    (ClassificationLevel.PUBLIC, RiskLevel.CRITICAL): (
        "POL-V1-PUBLIC-CRITICAL",
        (PolicyAction.BLOCK,),
    ),
    (ClassificationLevel.INTERNAL, RiskLevel.LOW): (
        "POL-V1-INTERNAL-LOW",
        (PolicyAction.ALLOW, PolicyAction.LOG),
    ),
    (ClassificationLevel.INTERNAL, RiskLevel.MEDIUM): (
        "POL-V1-INTERNAL-MEDIUM",
        (PolicyAction.WARN,),
    ),
    (ClassificationLevel.INTERNAL, RiskLevel.HIGH): (
        "POL-V1-INTERNAL-HIGH",
        (PolicyAction.REQUIRE_JUSTIFICATION,),
    ),
    (ClassificationLevel.INTERNAL, RiskLevel.CRITICAL): (
        "POL-V1-INTERNAL-CRITICAL",
        (PolicyAction.BLOCK, PolicyAction.ALERT),
    ),
    (ClassificationLevel.CONFIDENTIAL, RiskLevel.LOW): (
        "POL-V1-CONFIDENTIAL-LOW",
        (PolicyAction.RESTRICT_ACCESS,),
    ),
    (ClassificationLevel.CONFIDENTIAL, RiskLevel.MEDIUM): (
        "POL-V1-CONFIDENTIAL-MEDIUM",
        (PolicyAction.ENCRYPT, PolicyAction.LOG),
    ),
    (ClassificationLevel.CONFIDENTIAL, RiskLevel.HIGH): (
        "POL-V1-CONFIDENTIAL-HIGH",
        (PolicyAction.RESTRICT_ACCESS, PolicyAction.ALERT),
    ),
    (ClassificationLevel.CONFIDENTIAL, RiskLevel.CRITICAL): (
        "POL-V1-CONFIDENTIAL-CRITICAL",
        (PolicyAction.QUARANTINE, PolicyAction.ALERT),
    ),
    (ClassificationLevel.RESTRICTED, RiskLevel.LOW): (
        "POL-V1-RESTRICTED-LOW",
        (PolicyAction.RESTRICT_ACCESS, PolicyAction.ENCRYPT),
    ),
    (ClassificationLevel.RESTRICTED, RiskLevel.MEDIUM): (
        "POL-V1-RESTRICTED-MEDIUM",
        (PolicyAction.ALERT,),
    ),
    (ClassificationLevel.RESTRICTED, RiskLevel.HIGH): (
        "POL-V1-RESTRICTED-HIGH",
        (PolicyAction.BLOCK,),
    ),
    (ClassificationLevel.RESTRICTED, RiskLevel.CRITICAL): (
        "POL-V1-RESTRICTED-CRITICAL",
        (PolicyAction.QUARANTINE, PolicyAction.ALERT),
    ),
}


def apply_policy(
    classification: ClassificationResult,
    risk: RiskResult,
) -> PolicyResult:
    """Map classification and risk to advisory policy recommendations."""

    rule_id, actions = RULE_ACTIONS[(classification.level, risk.level)]
    review_reasons, review_rule_ids = _review_requirements(
        classification,
        risk,
        actions,
    )
    actions = _safe_actions(actions, bool(review_reasons))
    recommendations = _recommendations(
        actions,
        classification.level,
        risk.level,
    )

    if review_reasons:
        recommendations = (
            *recommendations,
            _recommendation(
                PolicyAction.HUMAN_REVIEW,
                is_primary=False,
                reason="An authorized analyst must review this advisory decision.",
            ),
        )

    return PolicyResult(
        policy_version=POLICY_VERSION,
        recommendations=recommendations,
        human_review_required=bool(review_reasons),
        review_reasons=tuple(review_reasons),
        triggered_rule_ids=(rule_id, *review_rule_ids),
    )


def _review_requirements(
    classification: ClassificationResult,
    risk: RiskResult,
    actions: tuple[PolicyAction, ...],
) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    rule_ids: list[str] = []

    def require(reason: str, rule_id: str) -> None:
        reasons.append(reason)
        rule_ids.append(rule_id)

    if risk.level is RiskLevel.CRITICAL:
        require(
            "Critical risk requires an authorized human decision.",
            "POL-V1-REVIEW-CRITICAL",
        )
    if classification.confidence < 70:
        require(
            "Classification confidence below 70 requires human review.",
            "POL-V1-REVIEW-LOW-CONFIDENCE",
        )
    if risk.triggered_overrides:
        require(
            "A risk override requires human review.",
            "POL-V1-REVIEW-RISK-OVERRIDE",
        )
    if any(
        action in {PolicyAction.BLOCK, PolicyAction.QUARANTINE}
        for action in actions
    ):
        require(
            "A Block or Quarantine recommendation requires human review.",
            "POL-V1-REVIEW-RESTRICTIVE-ACTION",
        )
    if (
        classification.level is ClassificationLevel.RESTRICTED
        and risk.level is RiskLevel.MEDIUM
    ):
        require(
            "Restricted content at medium risk requires monitored human review.",
            "POL-V1-REVIEW-RESTRICTED-MEDIUM",
        )

    return reasons, rule_ids


def _safe_actions(
    actions: tuple[PolicyAction, ...],
    human_review_required: bool,
) -> tuple[PolicyAction, ...]:
    """Keep ALLOW compatible with the v1 contract's recommendation rule."""

    if human_review_required and PolicyAction.ALLOW in actions:
        return (PolicyAction.WARN,)

    return actions


def _recommendations(
    actions: tuple[PolicyAction, ...],
    classification: ClassificationLevel,
    risk: RiskLevel,
) -> tuple[PolicyRecommendation, ...]:
    return tuple(
        _recommendation(
            action,
            is_primary=index == 0,
            reason=(
                f"{classification.value} classification with "
                f"{risk.value} risk requires {action.value} "
                f"under policy version {POLICY_VERSION}."
            ),
        )
        for index, action in enumerate(actions)
    )


def _recommendation(
    action: PolicyAction,
    *,
    is_primary: bool,
    reason: str,
) -> PolicyRecommendation:
    return PolicyRecommendation(
        action=action,
        execution_mode=(
            ExecutionMode.SIMULATED
            if action in SIMULATED_ACTIONS
            else ExecutionMode.RECOMMENDED
        ),
        is_primary=is_primary,
        reason=reason,
    )
