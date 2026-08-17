# Roadmap — GxP Change Control

## v1.0.0 baseline — complete

### Domain and API

- [x] Pydantic models for change requests, impact assessments, approvals, activity records, and stable validation errors
- [x] SQLite schema with synthetic seed records and foreign-key enforcement
- [x] FastAPI routes for intake, retrieval, filtering, submission, impact assessment, decisions, stage advancement, and activity review
- [x] Explicit server-side workflow transitions
- [x] Application-level append-oriented activity records with attributable actors and UTC timestamps
- [x] OpenAPI plus exported JSON Schemas
- [x] ISO date/date-time validation, IANA zones, DST fold detection, and nonexistent-time rejection

### Frontend

- [x] Change queue and status filtering
- [x] Validated change-request form
- [x] Impact checklist, residual-risk selection, and rationale entry
- [x] Approval, rejection, and request-for-information decisions
- [x] Implementation, verification, and close-out transitions
- [x] Recorded impact evidence and activity-history views
- [x] Ajv client validation with server-schema retrieval and local fallback

### Quality, governance, and release

- [x] 68 pytest tests across model, API, schema, time-zone, and full-workflow behavior
- [x] TypeScript type checking and Vite production build
- [x] Required CI aggregate gate
- [x] Bandit, `pip-audit`, and `npm audit`
- [x] CodeQL for Python and JavaScript/TypeScript
- [x] Optional SonarCloud/SonarQube workflow
- [x] Dockerfile and Docker Compose API profile
- [x] Security policy, MIT license, changelog, glossary, and portfolio-safety boundary
- [x] Idempotent GitHub release workflow gated on CI, CodeQL, and Sonar for the exact release SHA
- [x] Version-matched release notes with an explicit synthetic-data and non-validated-use boundary

## Post-v1.0 priorities

### Priority 1 — Identity and decision controls

- [ ] Add authentication and role-based authorization
- [ ] Define segregation-of-duties rules for requester, assessor, approver, implementer, and verifier
- [ ] Add configurable multi-approver matrices and rejection/resubmission policies
- [ ] Model electronic-signature meaning and re-authentication where applicable
- [ ] Add administrative user and role audit events

### Priority 2 — Execution evidence

- [ ] Add implementation-task records with owners, due dates, and completion evidence
- [ ] Add verification protocols, expected results, actual results, and reviewer disposition
- [ ] Support controlled evidence attachments with checksums and metadata
- [ ] Add change effectiveness review and post-implementation follow-up
- [ ] Export a human-reviewable change package and activity report

### Priority 3 — Data and platform hardening

- [ ] Introduce versioned database migrations and a PostgreSQL deployment profile
- [ ] Define backup, recovery, retention, archival, and periodic audit-review controls
- [ ] Add optimistic concurrency or equivalent protection against conflicting updates
- [ ] Add structured application logging, metrics, health dependencies, and alerting
- [ ] Add rate limiting, security headers, and deployment-specific CORS configuration

### Priority 4 — Test and delivery maturity

- [ ] Add browser-level end-to-end workflow tests
- [ ] Add accessibility checks and responsive visual regression coverage
- [ ] Add container image and secret scanning
- [ ] Add signed build provenance, artifact attestations, and optional release assets
- [ ] Add deployment documentation for a non-regulated demonstration environment

## Explicit non-goals for this portfolio release

- No use with production, personal, confidential, proprietary, or regulated records
- No claim of compliance, validation, certification, or fitness for a regulated intended use
- No replacement for approved SOPs, quality-unit decisions, formal assurance, or validated systems

## Design principles

1. Synthetic data only
2. Explainable status transitions with no hidden workflow state
3. Attributable actors and server-generated UTC timestamps
4. Validation at both client and server boundaries
5. Parameterized database access and controlled errors
6. Release tags tied to a gate-verified commit SHA
7. Explicit separation between technical demonstration and regulated use
