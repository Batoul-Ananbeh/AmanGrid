import pytest

from intelligence.classification import (
    ClassificationLevel,
    classify_document,
)
from intelligence.detection import detect_sensitive_data


def document(
    text: str,
    *,
    status: str = "complete",
    important_failure: bool = False,
) -> dict[str, object]:
    extraction: dict[str, object] = {
        "status": status,
        "important_failure": important_failure,
    }

    if status == "partial":
        extraction["issues"] = [
            "Synthetic table was unreadable.",
        ]

    return {
        "document_id": "doc-001",
        "text": text,
        "extraction": extraction,
    }


def classify(
    text: str,
    **kwargs: object,
):
    return classify_document(
        document(text, **kwargs),
        detect_sensitive_data(text),
    )


@pytest.mark.parametrize(
    ("text", "level"),
    [
        (
            "Published public notice for a community energy-awareness event.",
            ClassificationLevel.PUBLIC,
        ),
        (
            "Internal maintenance procedure for the facilities team.",
            ClassificationLevel.INTERNAL,
        ),
        (
            "Customer ID: CUST-001122",
            ClassificationLevel.CONFIDENTIAL,
        ),
        (
            "SCADA PLC configuration password=DemoSecret-77",
            ClassificationLevel.RESTRICTED,
        ),
    ],
)
def test_classifies_all_four_levels(
    text: str,
    level: ClassificationLevel,
) -> None:
    assert classify(text).level is level


def test_highest_sensitivity_wins_over_customer_data() -> None:
    result = classify(
        "Customer ID: CUST-001122. PLC host 10.1.2.3. "
        "access token=Demo-77"
    )

    assert result.level is ClassificationLevel.RESTRICTED
    assert result.confidence == 97


def test_absence_of_findings_is_not_public() -> None:
    result = classify(
        "A short note without enough context to determine distribution status."
    )

    assert result.level is ClassificationLevel.INTERNAL
    assert result.confidence == 55
    assert result.uncertainty_reasons == (
        "Insufficient context to classify the content as Public.",
    )


def test_partial_important_extraction_lowers_confidence() -> None:
    result = classify(
        "Customer ID: CUST-001122",
        status="partial",
        important_failure=True,
    )

    assert result.level is ClassificationLevel.CONFIDENTIAL
    assert result.confidence == 66
    assert result.uncertainty_reasons[-1] == (
        "Important partial extraction reduces classification confidence."
    )


def test_failed_extraction_cannot_be_classified() -> None:
    with pytest.raises(ValueError, match="failed extraction"):
        classify_document(
            {
                "extraction": {
                    "status": "failed",
                    "important_failure": True,
                }
            },
            detect_sensitive_data(""),
        )


def test_contract_fields_are_safe() -> None:
    secret = "DemoSecret-77"
    result = classify(f"SCADA host 10.1.2.3 password={secret}")
    fields = result.to_contract_fields()

    assert fields["classification"]["level"] == "Restricted"
    assert fields["energy_context"]["scada_ot_relevant"] is True
    assert fields["evidence"]
    assert all(item["masked"] is True for item in fields["evidence"])
    assert secret not in str(fields)


def test_classification_is_deterministic() -> None:
    text = "SCADA PLC uses 10.1.2.3 and password=DemoSecret-77"

    assert classify(text) == classify(text)
