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

Project baseline only; implementation has not started.

This repository currently contains the project baseline and documentation references; no application implementation, runtime stack, or production code has been created yet.

## Planned stack (planned and not implemented)

The following stack is planned for future implementation and is explicitly not implemented in the current repository:

- React/Vite
- Python/FastAPI
- PostgreSQL
- Alembic
- Pytest
- Vitest
- Docker Compose

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
