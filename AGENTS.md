# AmanGrid Repository Instructions

> Project-level instructions for AI coding agents and human contributors.
> Keep this file short and operational. Product detail remains in the referenced documents.

## 1. Source of Truth

Use this priority order when sources disagree:

1. Current Git state, code, and verified test results.
2. Explicit user instructions for the current task.
3. Repository instructions, including this file.
4. `AMANGRID_MASTER_CONTEXT_AND_TEAM_WORKFLOW_AR.md` for approved project and team decisions.
5. Product and design references under `docs/references/`.

Do not silently resolve a material conflict. Report both sources, impact, and recommendation.

## 2. Context-Efficient Session Bootstrap

At the beginning of every task:

1. Read this file completely.
2. Read `README.md`.
3. Read `docs/CURRENT_HANDOFF.md`.
4. Inspect the current branch, HEAD, `git status`, and recent relevant commits.
5. Read only the code and documentation relevant to the current Task ID.

Read `AMANGRID_MASTER_CONTEXT_AND_TEAM_WORKFLOW_AR.md` completely only when:

- starting a new milestone;
- defining or changing architecture, scope, ownership, contracts, or security policy;
- `docs/CURRENT_HANDOFF.md` is missing, stale, or insufficient;
- a conflict requires the approved planning baseline.

Read the PDFs under `docs/references/` only when the task needs product requirements, risk/classification policy, architecture diagrams, or UI/design details. Do not reload them for routine implementation, testing, Git, or documentation-only tasks.

Keep one Task ID per AI session. Start a new session when moving to a different task or phase.

## 3. Current Product Boundary

AmanGrid is a planned web MVP for explainable security analysis of energy-sector files and text. It supports analysis and decision guidance; it is not a production security enforcement platform.

MVP inputs:

- PDF.
- Word.
- Manual text.

Classification levels:

- `Public`
- `Internal`
- `Confidential`
- `Restricted`

DLP actions must always be represented as `RECOMMENDED` or `SIMULATED`. Never claim real enforcement.

Out of scope for the MVP:

- real SCADA/OT connections or control;
- enterprise DLP, SIEM, IAM, email, or cloud-storage integration;
- real company or customer sensitive data;
- a full multi-agent system.

## 4. Architecture and Ownership

Preferred MVP approach:

- Modular Monolith.
- Contract-First collaboration.
- Vertical Slices.
- One Hybrid Intelligence Engine with clear internal modules.

Ownership:

- Batoul owns the Application Stack: frontend, API orchestration, secure extraction, database/audit, and infrastructure.
- Mo'men owns the Intelligence Stack: detection, energy/SCADA context, classification, risk, policy, and AI evaluation.
- Integration tests and the End-to-End demo are shared checkpoints, but every task still has one owner.

Do not modify another owner's files without coordination.

## 5. Contract Rules

JSON Contracts are the integration boundary between both tracks.

- Every contract has an explicit version.
- Required, optional, nullable, and unknown behavior must be defined.
- Enums and numeric ranges must be validated.
- Do not invent unavailable metadata.
- Use synthetic fixtures only.
- Contract changes require review by both owners and a documented version impact.
- Mock fixtures must support independent frontend and intelligence development.

## 6. Security Rules

- Never commit secrets, tokens, credentials, `.env` contents, or real sensitive data.
- Mask sensitive evidence; never return or log a complete detected secret.
- Validate structured AI output before using it.
- Treat uploaded content as untrusted and account for prompt injection.
- Do not log full document contents unless a narrowly approved test requires synthetic content.
- Use bounded temporary file handling and documented cleanup.

## 7. Git and Change Safety

- Never work directly on `main`.
- Use one branch per task.
- One owner and one reviewer per task.
- Do not use force push, destructive reset, broad clean, or destructive file deletion.
- Do not commit or push unless the user explicitly requests it.
- Stage only explicit paths; do not use broad staging for a mixed working tree.
- Review the diff and validation evidence before delivery or merge.

## 8. Working Modes

- `READ ONLY`: inspect and report; no file changes.
- `PLAN`: produce a bounded plan; no implementation.
- `IMPLEMENT`: make the smallest scoped change and validate it.
- `DEBUG`: diagnose first, then fix the smallest verified cause.
- `REVIEW`: report findings before edits unless edits are explicitly requested.
- `FULL DELIVERY`: plan, implement, test, review, validate, and hand off; commit/push still require explicit permission.

## 9. Validation and Reporting

Do not say a task passed without evidence. Use the checks relevant to the actual stack and task, including schema validation, unit tests, lint, type checking, build, integration, security checks, or manual verification.

End every implementation session with:

```text
TASK:
BRANCH:
HEAD:
CHANGED:
TESTED:
PASSED:
NOT TESTED:
RISKS:
NEXT:
```

Update `docs/CURRENT_HANDOFF.md` when a task, branch, HEAD, test result, blocker, or next task materially changes.
