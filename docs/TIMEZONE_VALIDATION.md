# Timezone validation policy

## Policy string

`timezone-aware-required; storage-normalized-to-UTC`

## API stamps (change control records)

| Accepted | Rejected |
|----------|----------|
| `2026-08-17T12:00:00Z` | `2026-08-17T12:00:00` (naive) |
| `2026-08-17T08:00:00-04:00` | `08/17/2026 12:00 PM` |
| `2026-08-17T12:00:00+00:00` | Offsets outside **UTC−12 .. UTC+14** |

On validate/write, values are **normalized to UTC** (`+00:00`).

### Why

Audit-style activity logs need unambiguous instants. A naive local time without zone context is not attributable to a single moment (ALCOA *contemporaneous* teaching point — educational only).

## Calendar dates

`target_implementation_date` is **date-only** (`YYYY-MM-DD`) — no timezone. “Today” for past-checks uses **UTC date**.

## IANA zones (helper API)

For UI demos (e.g. Puerto Rico):

```http
GET  /meta/timezone-policy
GET  /meta/timezone/America/Puerto_Rico
POST /meta/timezone/to-utc
{ "local_iso": "2026-08-17T08:00:00", "iana_zone": "America/Puerto_Rico" }
→ { "utc_iso": "2026-08-17T12:00:00+00:00", ... }
```

Primary POST bodies still require **aware** ISO; the helper shows how local wall time + IANA zone becomes UTC.

## Code

- `app/datetime_validation.py` — parse, bounds, UTC normalize, IANA
- `app/routers/meta.py` — policy endpoints
- Tests: `tests/test_timezone_validation.py`
