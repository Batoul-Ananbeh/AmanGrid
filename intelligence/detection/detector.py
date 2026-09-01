"""Rule-based sensitive-data detection with bounded, masked evidence."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Callable, Iterable

from .models import DetectionFinding, DetectionResult, FindingType


MAX_EVIDENCE_PER_FINDING = 5
MAX_INPUT_CHARACTERS = 200_000

EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE
)
IPV4_CANDIDATE_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
CREDENTIAL_PATTERN = re.compile(
    r"\b(?P<label>password|passwd|api[ _-]?key|access[ _-]?token|secret)"
    r"\s*[:=]\s*(?P<value>[^\s,;]+)",
    re.IGNORECASE,
)
METER_LABEL_PATTERN = re.compile(
    r"\b(?:smart\s+)?meter\s+(?:id|number|no\.?)\s*[:#=-]?\s*"
    r"(?P<value>[A-Z0-9][A-Z0-9-]{5,})\b",
    re.IGNORECASE,
)
CUSTOMER_LABEL_PATTERN = re.compile(
    r"\b(?:customer|account)\s+(?:id|number|no\.?)\s*[:#=-]?\s*"
    r"(?P<value>[A-Z0-9][A-Z0-9-]{5,})\b",
    re.IGNORECASE,
)
EQUIPMENT_LABEL_PATTERN = re.compile(
    r"\b(?:equipment|asset)\s+(?:id|number|no\.?)\s*[:#=-]?\s*"
    r"(?P<value>[A-Z0-9][A-Z0-9-]{4,})\b",
    re.IGNORECASE,
)
METER_PREFIX_PATTERN = re.compile(r"\b(?P<value>MTR-[A-Z0-9-]{4,})\b", re.IGNORECASE)
CUSTOMER_PREFIX_PATTERN = re.compile(r"\b(?P<value>CUST-[A-Z0-9-]{4,})\b", re.IGNORECASE)
EQUIPMENT_PREFIX_PATTERN = re.compile(r"\b(?P<value>EQ-[A-Z0-9-]{3,})\b", re.IGNORECASE)
ENERGY_INDICATOR_PATTERN = re.compile(
    r"\bSCADA\b|\bOT\b|\bPLC\b|\bRTU\b|\bHMI\b|\bDCS\b|"
    r"\bsubstation\b|\bsmart\s+meter\b|\bfeeder\b",
    re.IGNORECASE,
)


def detect_sensitive_data(text: str) -> DetectionResult:
    """Detect supported synthetic patterns without returning source values.

    The caller must provide extracted, bounded text. Empty text produces no findings;
    non-string values are rejected rather than silently stringified.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if len(text) > MAX_INPUT_CHARACTERS:
        raise ValueError("text exceeds the 200000-character contract limit")

    findings = (
        _detect_emails(text),
        _detect_internal_ips(text),
        _detect_credentials(text),
        _detect_identifiers(
            text, METER_LABEL_PATTERN, METER_PREFIX_PATTERN, FindingType.METER_ID
        ),
        _detect_identifiers(
            text,
            CUSTOMER_LABEL_PATTERN,
            CUSTOMER_PREFIX_PATTERN,
            FindingType.CUSTOMER_ID,
        ),
        _detect_identifiers(
            text,
            EQUIPMENT_LABEL_PATTERN,
            EQUIPMENT_PREFIX_PATTERN,
            FindingType.EQUIPMENT_ID,
        ),
        _detect_energy_indicators(text),
    )
    return DetectionResult(findings=tuple(finding for finding in findings if finding))


def _detect_emails(text: str) -> DetectionFinding | None:
    matches = EMAIL_PATTERN.findall(text)
    return _finding(FindingType.EMAIL_ADDRESS, matches, _mask_email)


def _detect_internal_ips(text: str) -> DetectionFinding | None:
    matches = [
        candidate
        for candidate in IPV4_CANDIDATE_PATTERN.findall(text)
        if _is_internal_ipv4(candidate)
    ]
    return _finding(FindingType.INTERNAL_IP, matches, lambda _: "IP [REDACTED]")


def _detect_credentials(text: str) -> DetectionFinding | None:
    matches = list(CREDENTIAL_PATTERN.finditer(text))
    if not matches:
        return None
    evidence = _bounded_unique(
        f"{_normalise_label(match.group('label'))}=[REDACTED]" for match in matches
    )
    return DetectionFinding(FindingType.CREDENTIAL, len(matches), evidence)


def _detect_identifiers(
    text: str,
    label_pattern: re.Pattern[str],
    prefix_pattern: re.Pattern[str],
    finding_type: FindingType,
) -> DetectionFinding | None:
    matches: list[str] = []
    seen_value_spans: set[tuple[int, int]] = set()
    for match in label_pattern.finditer(text):
        matches.append(match.group("value"))
        seen_value_spans.add(match.span("value"))
    for match in prefix_pattern.finditer(text):
        if match.span("value") not in seen_value_spans:
            matches.append(match.group("value"))
    return _finding(finding_type, matches, lambda _: f"{finding_type.value} [REDACTED]")


def _detect_energy_indicators(text: str) -> DetectionFinding | None:
    matches = ENERGY_INDICATOR_PATTERN.findall(text)
    return _finding(
        FindingType.SCADA_OT_INDICATOR,
        matches,
        lambda value: f"Energy indicator: {value.upper()}",
    )


def _finding(
    finding_type: FindingType,
    matches: Iterable[str],
    mask: Callable[[str], str],
) -> DetectionFinding | None:
    values = list(matches)
    if not values:
        return None
    return DetectionFinding(
        type=finding_type,
        count=len(values),
        evidence=_bounded_unique(mask(value) for value in values),
    )


def _is_internal_ipv4(value: str) -> bool:
    try:
        address = ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        return False
    return (
        address in ipaddress.IPv4Network("10.0.0.0/8")
        or address in ipaddress.IPv4Network("172.16.0.0/12")
        or address in ipaddress.IPv4Network("192.168.0.0/16")
    )


def _mask_email(value: str) -> str:
    return f"{value[0]}***@***"


def _normalise_label(value: str) -> str:
    return re.sub(r"[ _-]+", "_", value).upper()


def _bounded_unique(values: Iterable[str]) -> tuple[str, ...]:
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
        if len(unique) == MAX_EVIDENCE_PER_FINDING:
            break
    return tuple(unique)
