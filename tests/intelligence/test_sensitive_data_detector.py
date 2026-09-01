import pytest

from intelligence.detection import FindingType, detect_sensitive_data


def findings_by_type(text: str):
    result = detect_sensitive_data(text)
    return {finding.type: finding for finding in result.findings}


def test_detects_supported_sensitive_and_energy_patterns_with_masked_evidence():
    text = """
    Contact operator.ahmad@example.test about meter ID: MTR-12345678.
    Customer ID: CUST-001122. Equipment ID: PLC-CTRL-99.
    SCADA PLC configuration uses 10.44.8.19. password = DemoSecret-77.
    """

    findings = findings_by_type(text)

    assert findings[FindingType.EMAIL_ADDRESS].count == 1
    assert findings[FindingType.INTERNAL_IP].count == 1
    assert findings[FindingType.CREDENTIAL].count == 1
    assert findings[FindingType.METER_ID].count == 1
    assert findings[FindingType.CUSTOMER_ID].count == 1
    assert findings[FindingType.EQUIPMENT_ID].count == 1
    assert findings[FindingType.SCADA_OT_INDICATOR].count == 3

    evidence = [item for finding in findings.values() for item in finding.evidence]
    assert "operator.ahmad@example.test" not in evidence
    assert "10.44.8.19" not in evidence
    assert "DemoSecret-77" not in evidence
    assert "MTR-12345678" not in evidence


def test_counts_all_occurrences_but_bounds_duplicate_evidence():
    findings = findings_by_type("a@example.test a@example.test a@example.test")

    email = findings[FindingType.EMAIL_ADDRESS]
    assert email.count == 3
    assert email.evidence == ("a***@***",)


def test_bounds_distinct_masked_evidence():
    text = "SCADA OT PLC RTU HMI DCS substation"

    energy = findings_by_type(text)[FindingType.SCADA_OT_INDICATOR]
    assert energy.count == 7
    assert len(energy.evidence) == 5


@pytest.mark.parametrize("address", ["8.8.8.8", "172.32.0.1", "192.0.2.10", "999.10.10.10"])
def test_does_not_classify_public_or_invalid_ipv4_as_internal(address):
    findings = findings_by_type(f"Observed address: {address}")

    assert FindingType.INTERNAL_IP not in findings


def test_detects_each_supported_internal_ipv4_range():
    findings = findings_by_type("10.0.0.8 172.20.4.3 192.168.1.12")

    internal_ips = findings[FindingType.INTERNAL_IP]
    assert internal_ips.count == 3
    assert internal_ips.evidence == ("IP [REDACTED]",)


def test_contract_findings_only_expose_type_and_count():
    result = detect_sensitive_data("SCADA host 10.1.2.3")

    assert result.contract_findings() == [
        {"type": "INTERNAL_IP", "count": 1},
        {"type": "SCADA_OT_INDICATOR", "count": 1},
    ]


def test_empty_text_produces_no_findings():
    assert detect_sensitive_data("   \n").findings == ()


def test_non_string_input_is_rejected():
    with pytest.raises(TypeError, match="text must be a string"):
        detect_sensitive_data(None)  # type: ignore[arg-type]


def test_detection_is_deterministic():
    text = "RTU credentials: access token=Token-123 10.9.8.7"

    assert detect_sensitive_data(text) == detect_sensitive_data(text)
