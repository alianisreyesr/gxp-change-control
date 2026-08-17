# DST fold detection (PEP 495)

## API helpers

```http
POST /meta/timezone/analyze
{ "local_iso": "2025-11-02T01:30:00", "iana_zone": "America/New_York" }

POST /meta/timezone/to-utc
{ "local_iso": "2025-11-02T01:30:00", "iana_zone": "America/New_York", "fold": 0 }
```

## Kinds

| kind | Meaning | Action |
|------|---------|--------|
| `unique` | One UTC instant | Convert freely |
| `ambiguous` | Fall-back overlap | Require `fold` 0 or 1 |
| `nonexistent` | Spring-forward gap | Reject (422) |

## fold

- `fold=0` — first occurrence (still on pre-transition offset)
- `fold=1` — second occurrence (post-transition offset)

## Demo dates (America/New_York, 2025)

- Gap: `2025-03-09T02:30:00`
- Ambiguous: `2025-11-02T01:30:00`

`America/Puerto_Rico` has **no DST** — wall times are unique year-round.

## Primary change-control stamps

Still **UTC / offset ISO only** — no naive local times on audit fields.
