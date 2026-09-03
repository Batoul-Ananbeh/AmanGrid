# AmanGrid

AmanGrid is a planned AI-powered data security application for the energy sector. It is designed for a Cybersecurity Analyst in an energy company to review files and text that may contain sensitive operational, customer, or infrastructure-related information, assess their classification and risk, and receive explainable guidance on the appropriate response before any wider handling or sharing decision is made.

## Product summary

AmanGrid is a planned web application intended to help a Cybersecurity Analyst analyze uploaded or manually entered content, extract text and metadata, detect sensitive patterns, understand the context of energy and OT/SCADA-related information, classify the content, assess risk, apply policy rules, recommend a protection action, and send uncertain or high-risk cases to human review. The project is intentionally scoped to an MVP that supports controlled review and decision support rather than operational enforcement.

## Primary user

Primary user: Cybersecurity Analyst in an energy company.

Secondary users may include security leadership, data owners, and operational teams, but the primary workflow and MVP scope are centered on the Cybersecurity Analyst.

## MVP workflow

Upload/Input -> Extract -> Detect -> Understand -> Classify -> Assess Risk -> Apply Policy -> Recommend Action -> Human Review

## Supported MVP inputs

- PDF
- Word
- Manual text entry

## Classification levels

- Public
- Internal
- Confidential
- Restricted

## DLP actions and execution model

DLP actions in the MVP are Recommended or Simulated only. They are not real enforcement actions against enterprise systems, SCADA/OT assets, email, storage platforms, or other production controls.

## Out of scope

The current MVP is intentionally out of scope for:

- Real SCADA/OT connection or operational control
- Enterprise DLP integration
- Real company or customer sensitive data
- Full multi-agent system deployment

## Team ownership

- Batoul owns Application Stack.
- Mo'men owns Intelligence Stack.
- JSON Contracts connect both tracks.

## Documentation

| Document | Purpose | Link |
| --- | --- | --- |
| AI Development Environment Starter | Environment and working rules | [AI_DEV_ENVIRONMENT_PROJECT_STARTER.md](./AI_DEV_ENVIRONMENT_PROJECT_STARTER.md) |
| Project Handoff and Team Workflow | Team workflow, ownership model, project context, and task sequencing | [AMANGRID_MASTER_CONTEXT_AND_TEAM_WORKFLOW_AR.md](./AMANGRID_MASTER_CONTEXT_AND_TEAM_WORKFLOW_AR.md) |
| AmanGrid Application 0.1 | Product concept, problem statement, user, MVP scope, and workflow | [docs/references/AmanGrid_Application_0.1_AR.pdf](./docs/references/AmanGrid_Application_0.1_AR.pdf) |
| AmanGrid Application Design 0.2 | Architecture, file journey, classification policy, risk model, DLP mapping, and UI mockups | [docs/references/AmanGrid_Application_Design_0.2_AR.pdf](./docs/references/AmanGrid_Application_Design_0.2_AR.pdf) |

## Current repository status

Implementation is in progress. The repository currently contains:

- draft v1 JSON contracts and synthetic fixture pairs;
- deterministic sensitive-data detection and classification modules;
- a FastAPI application skeleton with health and contract-validated demo paths;
- a responsive Arabic React/Vite application interface that verifies API connectivity and renders the contract-validated demo decision;
- PostgreSQL and full-stack local orchestration configuration;
- contract, intelligence, backend, and frontend tests.

Secure extraction, the real analysis lifecycle, persistence/migrations, authentication, and the complete analyst experience remain planned work. DLP actions remain recommendations or simulations only.

## Implemented stack baseline

| Area | Baseline |
| --- | --- |
| Frontend | React 19, TypeScript 7, Vite 8, Vitest 5 |
| Backend | Python 3.12, FastAPI 0.141, Uvicorn |
| Contract validation | JSON Schema Draft 2020-12 with `jsonschema` |
| Database service | PostgreSQL 18; schema and application wiring are deferred |
| Local orchestration | Docker Compose |
| Tests | Pytest and Vitest |

## Local development

Prerequisites are Python 3.12 and Node.js 24. Docker with Compose is optional unless the PostgreSQL service or the containerized full stack is needed. On Windows, Docker Desktop must have a working WSL 2 backend.

### Backend

From the repository root on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

The API is available at `http://localhost:8000`:

- `GET /api/v1/health` provides the smoke/health response.
- `GET /api/v1/demo/analysis` provides the synthetic Restricted/Critical fixture after validating it against `AnalysisDecision` v1.
- `/api/docs` provides local interactive API documentation.

### Frontend

In a second terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

The frontend is available at `http://localhost:5173` and reads `VITE_API_BASE_URL`, defaulting to `http://localhost:8000`.

### Full stack with Docker Compose

Docker is optional for the direct backend/frontend workflow. To start the frontend, backend, and PostgreSQL together:

```powershell
Copy-Item .env.example .env
# Replace POSTGRES_PASSWORD in .env with a local-only password.
docker compose up --build
```

No database schema or migration is created by this task; that belongs to the later database/history task.

## Validation commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Set-Location frontend
npm run typecheck
npm test
npm run build
```

## Working rules

- Work on a task branch.
- One owner per task.
- One reviewer per task.
- Tests and evidence are required before merge.

## First parallel tasks

- AG-M-001 Analysis Contracts and Test Fixtures
- AG-B-001 Application Skeleton

## Official project position

AmanGrid is a planned security analysis and decision-support prototype for energy-sector files and text. It is not a production security control, not an integrated enterprise DLP system, and not a full multi-agent platform. The system is scoped to support explainable classification, risk assessment, and recommendation workflows with human review as the final decision point.
