# World Cup Travel Atlas — Implementation Plan

## Phase 1: Project structure, dependencies, ingestion, dbt config
- [x] Repository structure and `.gitignore`
- [x] Python dependency management (`pyproject.toml`)
- [x] Frontend scaffolding (Vite + React + TypeScript)
- [x] Ingestion pipeline with retry, checksum, manifest
- [x] Small committed test fixtures
- [x] DuckDB / dbt configuration
- [x] Run ingestion against live OpenFootball source (1,069 matches)

## Phase 2: dbt models, Haversine, tests, venue seeds
- [x] Staging, intermediate, and mart models
- [x] Haversine macro with unit tests
- [x] Venue coordinate seed and alias tables (235 venues, 100% resolved)
- [x] dbt schema and singular tests
- [x] `dbt build` passes (44/44)

## Phase 3: FastAPI endpoints, schemas, API tests
- [x] Settings and database layer (read-only DuckDB)
- [x] Versioned API endpoints
- [x] Pydantic response models
- [x] Static file serving for production
- [x] API unit and integration tests (9 passed)

## Phase 4: React frontend
- [x] Filter controls with URL state
- [x] 3D globe with arcs and venue points
- [x] Total distance counter and replay
- [x] Itinerary table and CSV export
- [x] Data quality warnings and methodology drawer
- [x] Frontend unit tests (5 passed)

## Phase 5: Docker, Render, CI, documentation
- [x] Multi-stage Dockerfile with baseline DB
- [x] Startup refresh logic
- [x] `render.yaml` Blueprint
- [x] GitHub Actions CI workflow
- [x] Optional Render deploy-hook workflow
- [x] README and docs
- [ ] Playwright smoke test (requires production server + playwright install)
- [x] Final verification pass (Docker build blocked: Docker Desktop unavailable locally)

## Vertical slice milestone
- [x] 1930 Uruguay team route end-to-end
- [x] All 23 editions ingested and queryable
