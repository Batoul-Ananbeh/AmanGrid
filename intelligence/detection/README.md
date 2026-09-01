# Sensitive Data Detection

`detect_sensitive_data(text)` is a deterministic, rule-based entry point for already extracted text. It accepts a string of at most 200,000 characters, matching the `ExtractedDocument` v1 text limit. It rejects a longer value with `ValueError`; the Application Stack may validate the same bound before calling the detector.

Identifier detection intentionally requires one of two safe forms:

- an explicit label: `Meter ID`, `Smart Meter Number`, `Customer No`, `Account Number`, `Equipment ID`, or `Asset No`;
- an approved value prefix without a label: `MTR-`, `CUST-`, or `EQ-`.

Ordinary phrases such as `meter reading`, `customer service`, and `equipment status` are not identifiers.

## Contract and evidence adapters

`DetectionResult.contract_findings()` maps findings only to the current contract subset:

```json
{"type": "INTERNAL_IP", "count": 1}
```

It intentionally does not expose evidence. At the future decision-assembly boundary, each already-masked evidence string will map to the `AnalysisDecision.evidence` shape:

```json
{"type": "INTERNAL_IP", "excerpt": "IP [REDACTED]", "masked": true}
```

That adapter is not implemented in AG-M-002 because classification and decision assembly belong to later Intelligence Stack tasks. The detector never returns full secrets, identifiers, IP addresses, or source text as evidence.
