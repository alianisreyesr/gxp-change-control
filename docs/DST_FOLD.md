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

## Demo dates

### America/New_York (2025)

- Gap: `2025-03-09T02:30:00`
- Ambiguous: `2025-11-02T01:30:00`

### America/Puerto_Rico

No DST — wall times are always `unique`.

### Australia/Lord_Howe (complex / half-hour DST)

| Season (approx.) | Offset |
|------------------|--------|
| Southern winter | **UTC+10:30** |
| Southern summer | **UTC+11:00** |

DST step is **+30 minutes**, not +60. Parameterized tests: `tests/test_lord_howe.py`.

- Unique winter: `2025-07-15T12:00:00` → offset 10.5 h
- Unique summer: `2025-01-15T12:00:00` → offset 11 h
- Transition windows may be `unique` / `ambiguous` / `nonexistent` depending on tzdata; tests assert classification invariants (e.g. ambiguous pair differs by 30 minutes).

Aware API stamps with fractional offsets are valid:

```text
2025-07-15T01:30:00+10:30  → normalized UTC
```

## Primary change-control stamps

Still **UTC / offset ISO only** — no naive local times on audit fields.
