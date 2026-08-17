# Changelog

All notable changes to this portfolio project are documented in this file.

The project follows semantic versioning for public portfolio releases. Version numbers describe the repository's software baseline; they do not indicate regulatory validation, approval, or fitness for a regulated intended use.

## [1.0.0] — 2026-08-17

### Added

- Full change lifecycle from draft through impact assessment, approval, implementation, verification, and closure
- Explicit approval, rejection, and request-for-information decisions
- Structured impact assessment for validated state, Part 11 controls, data integrity, training, and SOPs
- Attributable actor validation and server-generated UTC activity timestamps
- React reviewer interface for intake, assessment, decisions, stage transitions, recorded impact evidence, and activity history
- FastAPI endpoints, OpenAPI documentation, and exported JSON Schemas
- Ajv Draft 2020-12 client validation with local schema fallback
- ISO date/date-time controls, IANA time-zone validation, DST fold handling, and nonexistent-time rejection
- SQLite schema with synthetic demonstration records
- Dockerfile and Docker Compose API profile
- Security policy, glossary, portfolio-safety boundary, and regulatory-reference documentation

### Quality and security

- 68 passing pytest tests across eight modules
- End-to-end API tests for approval, rejection, resubmission, request-for-information, closure, and invalid transitions
- TypeScript type checking and Vite production build in CI
- Bandit, `pip-audit`, and `npm audit` gates
- CodeQL analysis for Python and JavaScript/TypeScript
- Credential-aware SonarCloud/SonarQube workflow
- Non-root API container build

### Fixed

- Initialized isolated SQLite databases through FastAPI lifespan during API tests
- Correctly distinguished nonexistent spring-forward wall times from ambiguous fall-back times
- Aligned Bandit report generation with the documented medium-and-higher failure threshold
- Updated vulnerable Python dependency pins identified by `pip-audit`
- Replaced hard-coded demonstration decisions in the frontend with validated user-editable forms
- Improved client handling of FastAPI `detail` error responses

### Known limitations

- No authentication, role-based authorization, segregation of duties, or electronic signatures
- No dedicated implementation-task or verification-evidence records
- SQLite is intended for local demonstration, not governed multi-user operation
- Activity records are protected by application behavior, not an independently secured audit subsystem
- No controlled deployment, backup/recovery, retention, monitoring, or formal validation package
- Synthetic data only; not for real quality, release, compliance, or regulatory decisions
