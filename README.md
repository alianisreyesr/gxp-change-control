# GxP Change Control Tracker

<div align="center">

[![CI](https://github.com/alianisreyesr/gxp-change-control/actions/workflows/ci.yml/badge.svg)](https://github.com/alianisreyesr/gxp-change-control/actions/workflows/ci.yml)
[![CodeQL](https://github.com/alianisreyesr/gxp-change-control/actions/workflows/codeql.yml/badge.svg)](https://github.com/alianisreyesr/gxp-change-control/actions/workflows/codeql.yml)
![Release](https://img.shields.io/badge/release-v1.0.0-2ea44f?style=flat)
![Tests](https://img.shields.io/badge/tests-68%20passing-brightgreen?style=flat)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?style=flat&logo=vite&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-activity%20evidence-003B57?style=flat&logo=sqlite&logoColor=white)

**Change requests · Impact assessment · Approvals · Verification · Activity evidence**

*A portfolio-safe, full-stack prototype for controlled GxP-style change workflows*

[Screenshots](#portfolio-preview) · [Quick start](#quick-start) · [Case study](docs/CASE_STUDY.md) · [Workflow](#controlled-workflow) · [API](#api-surface) · [Quality gates](#validation-and-quality-gates) · [Security](SECURITY.md)

</div>

---

> **Data boundary:** Every record and scenario is synthetic. This repository contains no proprietary, personal, employer, production, or regulated data. It is **not validated software** and must not be used to approve real changes, support product release, or claim regulatory compliance.

---

## Portfolio preview

| Change queue | New controlled-change request |
|---|---|
| ![Synthetic change queue with priority and workflow status](docs/assets/dashboard.png) | ![Synthetic change request form](docs/assets/new-change.png) |

![Synthetic change detail with impact assessment and activity history](docs/assets/change-detail.png)

**[Watch the 60-second walkthrough](docs/assets/gxp-change-control-walkthrough.mp4)** · See the [case study](docs/CASE_STUDY.md) for the business problem, users, decisions, evidence, and production boundary.

## What this is

GxP Change Control Tracker models how a quality, CSV, data, or IT compliance team can structure a controlled software-change lifecycle:

- capture a specific change request and business justification;
- assess effects on validated state, Part 11 controls, data integrity, training, and SOPs;
- record an attributable approval, rejection, or request for more information;
- advance approved work through implementation, verification, and closure;
- retain an application-level append-oriented activity history with server-generated UTC timestamps.

The project is intentionally transparent. Status transitions are explicit, validation rules are version-controlled, and the frontend and API use compatible schemas. The system demonstrates engineering patterns; it does not replace procedural controls, quality-unit review, or formal validation.

## Controlled workflow

```mermaid
stateDiagram-v2
    direction LR
    [*] --> draft
    draft --> impact_assessment: submit
    impact_assessment --> pending_approval: submit assessment
    pending_approval --> approved: approve
    pending_approval --> rejected: reject
    pending_approval --> impact_assessment: request_info
    rejected --> impact_assessment: resubmit
    approved --> implementing: advance
    implementing --> verification: advance
    verification --> closed: advance
```

| Stage | Evidence captured |
|---|---|
| **Draft** | Title, description, system, type, priority, requester, justification, target date |
| **Impact assessment** | Five impact flags, residual risk, risk rationale, attributable assessor |
| **Decision** | Role, decision, comment when required, attributable approver |
| **Implementation / verification** | Controlled stage transitions with actor and timestamp |
| **Closure** | Final state plus complete activity history exposed through the API and UI |

## Main capabilities

| Area | What the repository demonstrates |
|---|---|
| **Change intake** | Validated creation form, priority rules, target-date controls, synthetic seed records |
| **Impact assessment** | Structured risk flags, residual-risk consistency rules, recorded assessor and rationale |
| **Approval control** | `approve`, `reject`, and `request_info` decisions with required comments where appropriate |
| **Workflow integrity** | Server-enforced transitions; invalid transitions return controlled errors and do not add evidence |
| **Traceability** | Activity records for creation, submission, assessment, decisions, and stage changes |
| **API contracts** | FastAPI + Pydantic v2, stable 422 validation body, OpenAPI, exported JSON Schemas |
| **Client validation** | Ajv Draft 2020-12 validation with local schema fallback and server-side revalidation |
| **Time integrity** | UTC normalization, IANA time-zone validation, DST fold/gap handling, server timestamps |
| **Delivery controls** | pytest, TypeScript, Vite build, Bandit, dependency audits, CodeQL, Docker build, optional Sonar scan |

## Architecture

```mermaid
flowchart TD
    UI["React 19 + TypeScript + Vite\nTanStack Query + Ajv schemas"]
    API["FastAPI + Pydantic v2\nDomain validation + workflow\nOpenAPI + JSON Schema routes"]
    DB[("SQLite\nchanges · impact assessments\napprovals · activity log")]

    UI -->|HTTP / JSON| API
    API -->|parameterized SQL| DB
```

See [docs/STACK.md](docs/STACK.md), [docs/VALIDATION.md](docs/VALIDATION.md), and [docs/JSON_SCHEMA.md](docs/JSON_SCHEMA.md).

## Quick start

### Option A — Docker for the API

```bash
git clone https://github.com/alianisreyesr/gxp-change-control.git
cd gxp-change-control
docker compose up --build
```

- Health: `http://127.0.0.1:8000/health`
- OpenAPI / Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

The Compose file runs the API and persists the synthetic SQLite database in a named volume. Run the frontend separately for the full UI.

```bash
cd frontend
npm install
npm run dev
# http://127.0.0.1:5173
```

Vite proxies `/api` to the API on port 8000.

### Option B — Local development

```bash
# API
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload

# UI, in another terminal
cd frontend
npm install
npm run dev
```

Never load real change-control records, employee identifiers, credentials, validation evidence, or regulated data into this prototype.

## API surface

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Service state, data classification, and application version |
| `/changes` | GET | List changes, optionally filtered by status |
| `/changes` | POST | Create a validated draft change request |
| `/changes/{id}` | GET | Retrieve one change |
| `/changes/{id}/submit` | POST | Submit a draft or rejected change for impact assessment |
| `/changes/{id}/impact` | GET / POST | Retrieve or record the impact assessment |
| `/changes/{id}/approve` | POST | Approve, reject, or request more information |
| `/changes/{id}/advance` | POST | Move approved work through implementation, verification, and closure |
| `/changes/{id}/activity` | GET | Retrieve newest-first activity evidence |
| `/schemas/{name}` | GET | Serve version-controlled request JSON Schemas |
| `/meta/timezone-policy` | GET | Explain timestamp, UTC, IANA-zone, fold, and gap rules |

## Validation and quality gates

The v1.0.0 baseline includes **68 passing pytest tests across eight test modules**. Coverage includes models, API validation, full workflow transitions, JSON Schema contracts, ISO date-time rules, DST folds and gaps, and non-hour DST transitions.

GitHub Actions gates changes with:

1. backend tests and coverage generation;
2. TypeScript type checking and a Vite production build;
3. Bandit SAST, `pip-audit`, and `npm audit`;
4. a Docker API image build;
5. CodeQL analysis for Python and JavaScript/TypeScript;
6. a Sonar workflow that runs when repository credentials are configured.

Run the principal checks locally:

```bash
pytest tests/ -v --cov=app --cov-report=term-missing

cd frontend
npm install
npm run typecheck
npm run build

# From the repository root
pip install "bandit[toml]" pip-audit
bandit -r app -c bandit.yaml -ll
pip-audit -r requirements.txt
cd frontend && npm audit --audit-level=high
```

See [docs/CI_CD.md](docs/CI_CD.md), [docs/SAST.md](docs/SAST.md), and [docs/CODEQL.md](docs/CODEQL.md).

## Repository structure

```text
gxp-change-control/
├── app/                    # FastAPI API, models, database helpers, routers
├── frontend/               # React + TypeScript reviewer interface
├── sql/                    # SQLite schema
├── schemas/                # Exported request JSON Schemas
├── scripts/                # Schema export utility
├── tests/                  # Unit, contract, integration, and workflow tests
├── docs/                   # Architecture-adjacent controls and references
├── .github/workflows/      # CI, CodeQL, and Sonar workflows
├── Dockerfile
├── docker-compose.yml
├── CHANGELOG.md
├── SECURITY.md
└── LICENSE
```

## Scope and production limitations

This release is suitable for portfolio review and local experimentation only. A real controlled system would additionally require, at minimum:

- identity management, authentication, role-based authorization, and segregation of duties;
- electronic-signature controls and signature meaning where applicable;
- multi-approver rules, delegation, escalation, and quality-unit governance;
- immutable or independently protected audit records, retention controls, and periodic review;
- controlled requirements, risk assessment, traceability, test evidence, approvals, and release records;
- database migrations, backup/recovery, monitoring, security assessment, and supported deployment environments;
- formal validation or assurance proportional to intended use and risk.

See [docs/PORTFOLIO_SAFETY.md](docs/PORTFOLIO_SAFETY.md) and [docs/ROADMAP.md](docs/ROADMAP.md).

## Regulatory context

The documentation uses GxP, data-integrity, Part 11, GAMP, and change-control vocabulary for educational mapping. These references provide context; they do not make the software compliant or validated. See [docs/REGULATORY_REFERENCES.md](docs/REGULATORY_REFERENCES.md).

---

## Regulated Portfolio Ecosystem

| Project | Domain Focus | Status |
|---|---|---|
| **[Quality Deviation Risk Monitor](https://github.com/alianisreyesr/quality-deviation-risk-monitor)** | Deviation prioritization & explainable risk scoring | ✅ Active · 57 tests |
| **[CSV Evidence Tracker](https://github.com/alianisreyesr/csv-evidence-tracker)** | Requirements traceability, IQ/OQ/PQ test execution, audit trail | ✅ Active · 27 tests |
| **[Data Integrity Case File](https://github.com/alianisreyesr/data-integrity-case-file)** | ALCOA+ investigation, CAPA readiness, local AI triage | ✅ Active |
| **[CSA Assurance Planner](https://github.com/alianisreyesr/csa-assurance-planner)** | Risk-based software assurance planning, FDA CSA alignment | ✅ Active |
| **[GxP Batch Data Pipeline](https://github.com/alianisreyesr/gxp-batch-data-pipeline)** | Batch manufacturing pipeline — DuckDB · dbt · Great Expectations | ✅ Active |

---

## License

Released under the [MIT License](LICENSE). The license permits use of the code; it does not certify fitness for regulated use.

---

<div align="center">

**Built by [Alianis Reyes-Reyes](https://www.linkedin.com/in/alianis-reyes-reyes/)**

Information Systems @ UPRM ·

*Change is inevitable — what matters is that it’s controlled, traceable, and evidence-based.*

</div>
