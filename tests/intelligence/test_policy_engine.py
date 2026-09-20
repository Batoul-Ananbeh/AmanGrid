import pytest

from intelligence.classification import (
    ClassificationLevel,
    ClassificationResult,
)
from intelligence.policy import (
    ExecutionMode,
    POLICY_VERSION,
    PolicyAction,
    apply_policy,
)
from intelligence.risk import RiskLevel, RiskResult


def classification(
    level: ClassificationLevel,
    *,
    confidence: int = 90,
) -> ClassificationResult:
    return ClassificationResult(
        level=level,
        confidence=confidence,
        explanation="Synthetic classification result.",
        scada_ot_relevant=level is ClassificationLevel.RESTRICTED,
        energy_summary="Synthetic energy context.",
        evidence=(),
        uncertainty_reasons=(),
    )


def risk(
    level: RiskLevel,
    *,
    overrides: tuple[str, ...] = (),
) -> RiskResult:
    return RiskResult(
        base_score=0,
        final_score=0,
        level=level,
        factors=(),
        triggered_overrides=overrides,
    )


@pytest.mark.parametrize(
    ("level", "risk_level", "actions", "review_required"),
    [
        (
            ClassificationLevel.PUBLIC,
            RiskLevel.LOW,
            (PolicyAction.ALLOW, PolicyAction.LOG),
            False,
        ),
        (
            ClassificationLevel.PUBLIC,
            RiskLevel.MEDIUM,
            (PolicyAction.WARN,),
            False,
        ),
        (
            ClassificationLevel.PUBLIC,
            RiskLevel.HIGH,
            (PolicyAction.WARN,),
            False,
        ),
        (
            ClassificationLevel.PUBLIC,
            RiskLevel.CRITICAL,
            (PolicyAction.BLOCK, PolicyAction.HUMAN_REVIEW),
            True,
        ),
        (
            ClassificationLevel.INTERNAL,
            RiskLevel.LOW,
            (PolicyAction.ALLOW, PolicyAction.LOG),
            False,
        ),
        (
            ClassificationLevel.INTERNAL,
            RiskLevel.MEDIUM,
            (PolicyAction.WARN,),
            False,
        ),
        (
            ClassificationLevel.INTERNAL,
            RiskLevel.HIGH,
            (PolicyAction.REQUIRE_JUSTIFICATION,),
            False,
        ),
        (
            ClassificationLevel.INTERNAL,
            RiskLevel.CRITICAL,
            (PolicyAction.BLOCK, PolicyAction.ALERT, PolicyAction.HUMAN_REVIEW),
            True,
        ),
        (
            ClassificationLevel.CONFIDENTIAL,
            RiskLevel.LOW,
            (PolicyAction.RESTRICT_ACCESS,),
            False,
        ),
        (
            ClassificationLevel.CONFIDENTIAL,
            RiskLevel.MEDIUM,
            (PolicyAction.ENCRYPT, PolicyAction.LOG),
            False,
        ),
        (
            ClassificationLevel.CONFIDENTIAL,
            RiskLevel.HIGH,
            (PolicyAction.RESTRICT_ACCESS, PolicyAction.ALERT),
            False,
        ),
        (
            ClassificationLevel.CONFIDENTIAL,
            RiskLevel.CRITICAL,
            (
                PolicyAction.QUARANTINE,
                PolicyAction.ALERT,
                PolicyAction.HUMAN_REVIEW,
            ),
            True,
        ),
        (
            ClassificationLevel.RESTRICTED,
            RiskLevel.LOW,
            (PolicyAction.RESTRICT_ACCESS, PolicyAction.ENCRYPT),
            False,
        ),
        (
            ClassificationLevel.RESTRICTED,
            RiskLevel.MEDIUM,
            (PolicyAction.ALERT, PolicyAction.HUMAN_REVIEW),
            True,
        ),
        (
            ClassificationLevel.RESTRICTED,
            RiskLevel.HIGH,
            (PolicyAction.BLOCK, PolicyAction.HUMAN_REVIEW),
            True,
        ),
        (
            ClassificationLevel.RESTRICTED,
            RiskLevel.CRITICAL,
            (
                PolicyAction.QUARANTINE,
                PolicyAction.ALERT,
                PolicyAction.HUMAN_REVIEW,
            ),
            True,
        ),
    ],
)
def test_policy_matrix(
    level: ClassificationLevel,
    risk_level: RiskLevel,
    actions: tuple[PolicyAction, ...],
    review_required: bool,
) -> None:
    result = apply_policy(classification(level), risk(risk_level))

    assert tuple(item.action for item in result.recommendations) == actions
    assert result.human_review_required is review_required
    assert sum(item.is_primary for item in result.recommendations) == 1
    assert result.recommendations[0].is_primary is True


def test_low_confidence_requires_human_review() -> None:
    result = apply_policy(
        classification(ClassificationLevel.INTERNAL, confidence=69),
        risk(RiskLevel.MEDIUM),
    )

    assert result.human_review_required is True
    assert "POL-V1-REVIEW-LOW-CONFIDENCE" in result.triggered_rule_ids
    assert result.recommendations[-1].action is PolicyAction.HUMAN_REVIEW


def test_risk_override_requires_human_review() -> None:
    result = apply_policy(
        classification(ClassificationLevel.CONFIDENTIAL),
        risk(RiskLevel.HIGH, overrides=("DRAFT-CREDENTIAL-UNENCRYPTED",)),
    )

    assert result.human_review_required is True
    assert "POL-V1-REVIEW-RISK-OVERRIDE" in result.triggered_rule_ids


def test_review_escalates_allow_without_mixing_allow_actions() -> None:
    result = apply_policy(
        classification(ClassificationLevel.PUBLIC),
        risk(RiskLevel.LOW, overrides=("DRAFT-TEST-OVERRIDE",)),
    )

    assert tuple(item.action for item in result.recommendations) == (
        PolicyAction.WARN,
        PolicyAction.HUMAN_REVIEW,
    )
    assert all(
        item.action is not PolicyAction.ALLOW
        for item in result.recommendations
    )


def test_restrictive_actions_are_simulated() -> None:
    result = apply_policy(
        classification(ClassificationLevel.RESTRICTED),
        risk(RiskLevel.CRITICAL),
    )
    modes = {
        item.action: item.execution_mode
        for item in result.recommendations
    }

    assert modes[PolicyAction.QUARANTINE] is ExecutionMode.SIMULATED
    assert modes[PolicyAction.ALERT] is ExecutionMode.RECOMMENDED


def test_contract_fields_are_schema_shaped() -> None:
    result = apply_policy(
        classification(ClassificationLevel.RESTRICTED),
        risk(RiskLevel.CRITICAL),
    )
    fields = result.to_contract_fields()
    policy = fields["policy"]

    assert result.policy_version == POLICY_VERSION
    assert set(policy) == {
        "recommendations",
        "human_review_required",
        "review_reasons",
        "triggered_rule_ids",
    }
    assert sum(
        item["is_primary"]
        for item in policy["recommendations"]
    ) == 1
    assert "policy_version" not in policy


def test_policy_is_deterministic() -> None:
    classification_result = classification(ClassificationLevel.CONFIDENTIAL)
    risk_result = risk(RiskLevel.HIGH)

    assert apply_policy(classification_result, risk_result) == apply_policy(
        classification_result,
        risk_result,
    )
