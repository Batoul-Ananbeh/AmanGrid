from intelligence.classification import classify_document
from intelligence.detection import detect_sensitive_data
from intelligence.risk import RiskLevel, RiskSeverity, assess_risk


def document(
    text: str,
    *,
    security_context: dict[str, object] | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "document_id": "doc-risk-001",
        "text": text,
        "extraction": {
            "status": "complete",
            "important_failure": False,
        },
    }

    if security_context is not None:
        result["security_context"] = security_context

    return result


def assess(
    text: str,
    *,
    security_context: dict[str, object] | None = None,
):
    extracted_document = document(
        text,
        security_context=security_context,
    )
    detection = detect_sensitive_data(text)
    classification = classify_document(extracted_document, detection)

    return assess_risk(
        extracted_document,
        classification,
        detection,
    )


def test_restricted_ot_external_context_matches_reference_score() -> None:
    result = assess(
        "SCADA PLC maintenance uses internal host 10.1.2.3 "
        "and password=DemoSecret-77.",
        security_context={
            "storage_location": "personal_cloud",
            "encryption_status": "not_encrypted",
            "sharing_scope": "external",
            "users_with_access": 12,
        },
    )

    assert result.base_score == 88
    assert result.final_score == 92
    assert result.level is RiskLevel.CRITICAL
    assert result.triggered_overrides == (
        "DRAFT-SCADA-CREDENTIAL",
        "DRAFT-RESTRICTED-EXTERNAL",
    )
    assert len(result.factors) == 6


def test_public_approved_encrypted_private_document_is_low_risk() -> None:
    result = assess(
        "Published public notice for a community energy-awareness event.",
        security_context={
            "storage_location": "approved_repository",
            "encryption_status": "encrypted",
            "sharing_scope": "private",
            "users_with_access": 1,
        },
    )

    assert result.base_score == 4
    assert result.final_score == 4
    assert result.level is RiskLevel.LOW
    assert result.triggered_overrides == ()


def test_missing_security_context_is_unknown_not_invented() -> None:
    result = assess("Customer ID: CUST-001122")

    factors = {factor.factor_id: factor for factor in result.factors}

    assert factors["exposure_level"].severity is RiskSeverity.UNKNOWN
    assert factors["access_scope"].severity is RiskSeverity.UNKNOWN
    assert factors["storage_compliance"].severity is RiskSeverity.UNKNOWN
    assert factors["protection_gap"].severity is RiskSeverity.UNKNOWN
    assert result.base_score == 24


def test_restricted_external_override_is_critical() -> None:
    result = assess(
        "SCADA operational note without credential-like access data.",
        security_context={
            "storage_location": "approved_repository",
            "encryption_status": "encrypted",
            "sharing_scope": "external",
            "users_with_access": 1,
        },
    )

    assert result.base_score == 63
    assert result.final_score == 92
    assert result.level is RiskLevel.CRITICAL
    assert result.triggered_overrides == (
        "DRAFT-RESTRICTED-EXTERNAL",
    )


def test_risk_contract_fields_are_safe_and_schema_shaped() -> None:
    secret = "DemoSecret-77"
    result = assess(
        f"SCADA PLC password={secret}",
        security_context={
            "storage_location": "personal_cloud",
            "encryption_status": "not_encrypted",
            "sharing_scope": "external",
            "users_with_access": 12,
        },
    )

    fields = result.to_contract_fields()

    assert fields["risk"]["base_score"] == 88
    assert fields["risk"]["final_score"] == 92
    assert fields["risk"]["level"] == "Critical"
    assert len(fields["risk"]["factors"]) == 6
    assert secret not in str(fields)


def test_risk_assessment_is_deterministic() -> None:
    text = "SCADA PLC uses 10.1.2.3 and password=DemoSecret-77"
    context = {
        "storage_location": "personal_cloud",
        "encryption_status": "not_encrypted",
        "sharing_scope": "external",
        "users_with_access": 12,
    }

    assert assess(text, security_context=context) == assess(
        text,
        security_context=context,
    )