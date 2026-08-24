# Case study: controlled change from request to verification

## Problem

Change records in regulated environments must make impact, ownership, approval, and post-change verification easy to reconstruct. A generic ticket board does not make those controls explicit.

## Users and outcome

Requesters capture the proposed change, reviewers assess impact, approvers make attributable decisions, and quality reviewers verify closure. The prototype turns that lifecycle into an explicit state machine with a durable UTC activity history.

## Engineering decisions

- FastAPI owns workflow validation so clients cannot bypass transition rules.
- React and TypeScript provide role-oriented forms and compatible API contracts.
- SQLite keeps the portfolio demo reproducible; Docker and CI make execution repeatable.
- Append-oriented history preserves who did what and when without presenting it as a validated audit trail.

## Evidence

The repository includes automated tests, CI, CodeQL, release automation, security guidance, architecture documentation, and a tagged `v1.0.0` release.

## Boundary

All records are synthetic. Production use would require governed identity, electronic-signature controls where applicable, validated infrastructure, approved procedures, formal validation evidence, monitoring, backup/recovery, and organizational quality oversight.
