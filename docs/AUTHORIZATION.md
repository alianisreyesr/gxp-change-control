# Authentication and authorization

The portfolio demo issues HS256 JWTs from `POST /auth/token`. Lifetime comes from `JWT_EXPIRES_MINUTES` (default 60) and the `expires_in` field of the login response reports the same value in seconds.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `JWT_SECRET_KEY` | none | HS256 signing key. **Required (at least 32 characters) when `ENVIRONMENT` is `production`, `prod` or `staging`; the API refuses to start otherwise.** In development an ephemeral random key is generated with a warning, so tokens reset on restart and do not work across workers. |
| `ENVIRONMENT` | `development` | Selects the strict secret check above. |
| `JWT_EXPIRES_MINUTES` | `60` | Token lifetime. |
| `LOGIN_MAX_ATTEMPTS` | `5` | Failed logins per client IP + username before HTTP 429. |
| `LOGIN_WINDOW_SECONDS` | `300` | Sliding window for the failed-login limit. |

The login throttle is in-process; a multi-worker deployment needs a shared store or a rate-limiting proxy. Throttled attempts are recorded as `login_throttled` security events and usernames are sanitised before they are logged.

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
