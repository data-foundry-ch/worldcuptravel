# Methodology

This document defines how World Cup Travel Atlas measures team travel, which data is included or excluded, and how edge cases are handled.

## Core metric

**Approximate match-location travel** is defined as:

> The sum of minimum great-circle (Haversine) distances between consecutive match locations in chronological order for a national team within a single FIFA Men's World Cup tournament.

This is implemented identically in:
- dbt (`int_team_travel_legs` → `agg_team_tournament_travel`)
- API (`METRIC_DEFINITION` in `app/services/routes.py`)
- Frontend methodology drawer

It is **not** a measure of:
- Actual flights or ground transport
- Distance from a team base camp or training site
- Travel between tournaments or across World Cup cycles
- Fan or official delegation travel

## Haversine formula

Great-circle distance uses the haversine formula with WGS84 mean Earth radius:

```
a = sin²(Δφ/2) + cos(φ1) × cos(φ2) × sin²(Δλ/2)
c = 2 × atan2(√a, √(1−a))
d = R × c
```

Where:
- φ = latitude in radians
- λ = longitude in radians
- **R = 6,371.0088 km** (`earth_radius_km` dbt var)

Implementation: `analytics/macros/haversine_km.sql`

### Special cases

| Case | Distance |
|------|----------|
| First match in sequence | 0 km (no prior leg) |
| Same lat/lng as previous match | 0 km |
| Missing coordinates on either endpoint | NULL → leg excluded from totals |
| `coordinate_precision = 'unresolved'` | Treated as missing |

## Chronological ordering

Matches are ordered per `(tournament_year, team_id)` by:

1. `match_date` (ascending)
2. `kickoff_time_raw` (when present)
3. `source_match_index` (stable tiebreaker from ingestion order)

`sequence_number` starts at 1 for each team's first match. Leg `n` connects sequence `n` to sequence `n+1`.

## Scopes

The `/api/v1/routes` endpoint accepts `scope`:

### `played` (default)

- Includes only matches where `is_played = true`
- Legs require the destination match to be played
- Used for historical analysis of completed tournaments

### `all`

- Includes scheduled fixtures (`is_played = false`)
- Legs involving unplayed matches are flagged `is_projected = true`
- **2026 warning:** API adds explicit warning that distances are projected itinerary travel

## Distance aggregates

Per team per tournament (`agg_team_tournament_travel`):

| Field | Definition |
|-------|------------|
| `total_distance_km` | Sum of all legs with complete coordinates |
| `completed_distance_km` | Sum where neither endpoint is projected (both played) |
| `projected_additional_distance_km` | Sum where at least one endpoint is unplayed |

Leaderboard ranking uses `total_distance_km` descending, with `team_name` as tiebreaker.

## Coordinate precision

Venues carry a `coordinate_precision` label:

| Value | Meaning |
|-------|---------|
| `stadium` | Stadium-level coordinates from curated reference |
| `city` | City centroid when stadium unknown |
| `metro` | Metropolitan area approximation |
| `approximate` | Best-effort geographic estimate |
| `unresolved` | No usable coordinates — excluded from totals |

**Current dataset:** 235 venues, all resolved (no `unresolved` rows in production seed).

## Exclusion rules

### Legs excluded from distance totals

A leg is excluded when `is_coordinate_complete = false`:
- Either endpoint lacks latitude/longitude
- Either endpoint has `coordinate_precision = 'unresolved'`

Excluded legs still appear in API responses with `excluded_from_total: true` and `exclusion_reason: "Incomplete coordinates"`.

### Matches excluded from totals

A match is flagged when coordinates are unresolved. The API sets `excluded_from_total: true` on affected `MatchLocation` rows.

### Cumulative distance

`cumulative_distance_km` on appearances and legs is a running sum of **included** legs only. Incomplete legs contribute 0 to the running total.

## Data sources

### Match facts

- **Source:** [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json)
- **Ref:** `master` (configurable via `OPENFOOTBALL_GITHUB_REF`)
- **Fields used:** teams, date, round, ground, scores, group
- **Played detection:** Scores present → played; otherwise scheduled

### Venue coordinates

- Manually curated in `scripts/venue_reference_data.json`
- Compiled to `analytics/seeds/venue_coordinates.csv`
- Not derived automatically from geocoding APIs at runtime

See [venue-enrichment.md](venue-enrichment.md).

## Team identity

Team IDs are canonicalized via `team_aliases` seed:
- Default: normalized raw team name from OpenFootball
- Alias override: stable `team_id` + `team_name_canonical` per tournament year

This handles spelling variants (e.g. "Korea Republic" vs "South Korea") within a tournament context.

## Data freshness

`/api/v1/meta` exposes:
- `last_successful_download_timestamp` — from `ingestion_manifest.json`
- `last_successful_dbt_build_timestamp` — from `dbt_build_meta.json`
- `is_data_stale` — true when last download is older than `DATA_FRESHNESS_WARNING_HOURS` (default 36)

The frontend `DataQualityBanner` surfaces stale-data warnings to users.

## Validation

### dbt singular tests

Enforce invariants documented above: non-negative distances, monotonic cumulative totals, unique sequences, valid coordinate ranges, scheduled matches unplayed.

### Python unit tests

- `tests/unit/test_haversine.py` — formula parity with dbt macro
- `tests/unit/test_ingestion.py` — match ID determinism, scheduled match handling

### Frontend unit tests

- `frontend/src/utils/haversine.test.ts` — client-side distance helper
- `frontend/src/utils/routeTransform.test.ts` — API response → globe arc transform

## Known methodological limitations

1. **City-level fallback** — When only city coordinates exist, consecutive matches in the same city but different stadiums may show 0 km incorrectly.
2. **Multi-host nations** — 2002 (Japan/Korea), 2026 (USA/Mexico/Canada) rely on per-match `raw_ground` text; cross-border legs reflect straight-line distance between resolved points.
3. **Neutral venues** — Matches are attributed to listed grounds; no adjustment for "home" advantage geography.
4. **Extra time / replays** — Each fixture is one row; replayed matches (e.g. 1934 Austria vs Germany) appear as separate sequence entries if both are in the source.
5. **2026 schedule changes** — Projected distances will change if FIFA revises venues or fixtures in OpenFootball.

## Example: Uruguay 1930

The integration test `test_route_uruguay_1930` verifies:
- Team list returns Uruguay for 1930
- Route with `scope=played` returns ≥ 1 match
- `total_distance_km >= 0`
- Match count matches locations array length

This is the canonical end-to-end vertical slice for the 1930 host nation.
