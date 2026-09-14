# Authentication and authorization

The portfolio demo issues one-hour HS256 JWTs from `POST /auth/token`. A random signing secret is generated at process start for local use; deployments must set `JWT_SECRET_KEY` so sessions survive restarts and tokens are isolated per environment.

## Demo accounts

| Username | Password | Role |
|---|---|---|
| `requester.demo` | `RequesterDemo!2026` | requester |
| `assessor.demo` | `AssessorDemo!2026` | assessor |
| `quality.demo` | `QualityDemo!2026` | quality approver |
| `implementer.demo` | `ImplementerDemo!2026` | implementer |
| `verifier.demo` | `VerifierDemo!2026` | verifier |
| `admin.demo` | `AdminDemo!2026` | administrator |

These identities and passwords are intentionally synthetic and must never be copied into a production deployment. Only PBKDF2 hashes are stored in application code.

## Transition matrix

| Action | Allowed role |
|---|---|
| Create or submit a change | requester |
| Record impact assessment | assessor |
| Approve, reject, request information | quality approver |
| Approved → implementing | implementer |
| Implementing → verification | verifier |
| Verification → closed | verifier |
| Review security events | administrator |

Administrators may execute workflow actions for demonstration and recovery. Non-admin actors must match the authenticated JWT subject. A requester cannot approve their own change even if they are issued an approver role. Failed authentication and role checks are appended to `security_events`.

## Production boundary

Production use would replace demo identities with an OIDC provider, MFA, managed signing keys, refresh-token rotation, account provisioning/deprovisioning, and formal validation evidence.
