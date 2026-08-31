# AmanGrid analysis contracts v1 - DRAFT

These Draft 2020-12 JSON Schemas define the boundary between secure input/extraction and the AmanGrid intelligence result. They are draft artifacts for AG-M-001; `contract_version: "1.0"` identifies the proposed wire format and does not mean Contract Freeze v1 has occurred.

## Contracts

- `ExtractedDocument` is the input produced after PDF, Word, or manual-text handling. It reports extraction state and includes only metadata the producer actually knows.
- `AnalysisDecision` is an explainable classification, risk summary, and recommended or simulated policy result. It is decision guidance, not real DLP enforcement.

Every object defined by these schemas rejects undeclared fields with `additionalProperties: false`. Consumers must validate data before use.

## Required and optional fields

`ExtractedDocument` requires `contract_version`, `document_id`, `input_kind`, and `extraction`. Usable `text` means a string containing at least one non-whitespace character; it is required for `complete` and `partial` extraction and forbidden for `failed` extraction. `file_metadata` and `security_context` are optional containers; their child fields are also optional so producers can omit unavailable values. `manual_text` forbids `file_metadata` to prevent fabricated file names, MIME types, sizes, dates, or page counts. When a MIME type is supplied, it must match the PDF or Word input kind.

`AnalysisDecision` requires identity fields plus `classification`, `sensitive_findings`, `energy_context`, `evidence`, `risk`, and `policy`. Its nested fields are required where the frontend needs a stable renderable shape. Empty findings, evidence, override, and `triggered_rule_ids` arrays are valid when no entries apply; `review_reasons` is empty only when human review is not required. `policy.triggered_rule_ids` contains unique bounded stable uppercase policy-rule IDs, such as `PUBLIC-01`, when a rule informs the recommendation.

JSON `null` is not accepted. Unavailable optional data is omitted. `unknown` is allowed only for domain states where absence and an explicitly unknown state differ: selected security-context values and a risk factor's severity. It is not a substitute for missing IDs, text, scores, classifications, or risk levels.

## Extraction behavior

- `complete`: requires usable text containing at least one non-whitespace character.
- `partial`: requires usable text containing at least one non-whitespace character and at least one bounded issue description. Analysis may continue only because usable text exists.
- `failed`: requires a bounded failure reason, forbids text, and must not produce an `AnalysisDecision`.

The pair-level tests require `policy.human_review_required: true` and a review reason when a partial extraction reports `important_failure: true`. A failed extraction cannot be represented as a fixture pair because no decision is permitted.

## Evidence safety

Evidence items require `masked: true`, and every excerpt is limited to 160 characters. Producers must supply synthetic test data and must replace complete secrets, credentials, customer data, or other sensitive values with visibly masked tokens. Neither contract authorizes logging full input text or evidence.

## Risk factors

`risk.factors` is a generic frontend-oriented list of stable IDs, labels, severities, and explanations. The three fixtures use the six current AmanGrid factors: Data Sensitivity, Operational Impact, Exposure Level, Access Scope, Storage Compliance, and Protection Gap. Fixture scores are illustrative contract data only; these schemas do not implement weights, numeric contributions, normalization, overrides, or the final scoring engine.

The schema enforces the approved `final_score` to risk-level bands: 0-24 Low, 25-49 Medium, 50-74 High, and 75-100 Critical. Test-layer semantic validation additionally rejects a final score below its base score and duplicate `risk.factors[].factor_id` values; these are payload relationships intentionally kept outside the scoring implementation owned by AG-M-004.

## Policy and human review

`policy.triggered_rule_ids` identifies the policy rules that informed the decision; an empty array means no policy rule applies. Human review requires a non-empty review reason and a `HUMAN_REVIEW` recommendation. When review is not required, reasons must be empty and that recommendation must be absent. `ALLOW` may only appear alone or with `LOG`. The schema also requires human review for Critical risk, confidence below 70, or one or more triggered overrides. All recommendations remain guidance or simulation through `RECOMMENDED` or `SIMULATED` execution modes; no enforcement is implied.

## Versioning and forward compatibility

The directory identifies the schema family (`contracts/v1/`), while `contract_version` identifies the proposed payload version (`1.0`). Breaking changes require a reviewed version impact and a new compatible version path or value. Because unknown properties are rejected, additive fields also require coordinated schema and consumer updates. Consumers should branch on `contract_version`, validate against the matching schema, and avoid inferring fields that are absent.

## Pending Batoul consumer review

Before any Contract Freeze v1, Batoul must confirm the Application Stack can produce and consume the proposed identifiers, input-kind values, optional file/security metadata, extraction issue shape, confidence and score units, evidence shape, risk-factor presentation, recommendation vocabulary, and review-reason behavior. Naming, field optionality, empty-array handling, and API serialization/error conventions remain draft pending that review.
