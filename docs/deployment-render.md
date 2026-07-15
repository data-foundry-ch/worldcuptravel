# Deployment on Render

This guide covers deploying World Cup Travel Atlas to [Render](https://render.com) using the included Blueprint (`render.yaml`) and Docker image.

## Prerequisites

- GitHub repository with this codebase pushed
- Render account (free tier supported)
- Optional: Render deploy hook URL for scheduled refreshes

## Current Deploy Readiness

Verified on Windows with Docker Desktop on 2026-07-15:

| Check | Result |
|-------|--------|
| Python lint | `ruff check app tests scripts` passed |
| Python typecheck | `mypy app` passed |
| Python tests | `11 passed` |
| Frontend lint | `npm run lint` passed |
| Frontend tests | `9 passed` |
| Frontend production build | `npm run build` passed |
| Docker build | `docker build -t worldcup-travel-atlas:render-check .` passed |
| Docker baseline startup | `/healthz` returned `status: ok`, `data_timestamp: 2026` |
| Docker refresh startup | `REFRESH_DATA_ON_START=true` returned `status: ok`, `data_timestamp: 2026` |

## Architecture on Render

```mermaid
flowchart TB
    GH[GitHub] -->|push / autoDeploy| BP[Render Blueprint]
    BP --> WS[Web Service<br/>worldcup-travel-atlas]
    WS --> DK[Docker build]
    DK --> C[Container :10000]
    C --> SH[start.sh → uvicorn]
    SH --> INIT[initialize_runtime]
    INIT --> BASE[/app/data/bootstrap/worldcup.duckdb]
    INIT --> TMP[/tmp/worldcup.duckdb]
    INIT -->|REFRESH_DATA_ON_START| REF[refresh_pipeline]
    REF --> OF[OpenFootball GitHub]
    SH --> HZ[/healthz]
```

## Exact Deployment Steps

### 1. Confirm required files exist locally

Run from the repository root:

```powershell
Test-Path .\render.yaml
Test-Path .\Dockerfile
Test-Path .\start.sh
Test-Path .\data\bootstrap\worldcup.duckdb
Test-Path .\frontend\public\earth_at_night.jpg
Test-Path .\frontend\public\logo.png
```

Each command should print `True`.

### 2. Run the local deploy checks

```powershell
.\.venv\Scripts\python -m ruff check app tests scripts
.\.venv\Scripts\python -m mypy app
.\.venv\Scripts\python -m pytest tests -q
cd frontend
npm run lint
npm run test
npm run build
cd ..
docker build -t worldcup-travel-atlas:render-check .
```

Optional container smoke test:

```powershell
docker run --rm -p 10000:10000 -e PORT=10000 -e REFRESH_DATA_ON_START=false worldcup-travel-atlas:render-check
```

In a second terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:10000/healthz
```

Expected: `status` is `ok`, `database_available` is `true`, and `data_timestamp` is `2026`.

### 3. Commit and push to GitHub

If this folder is not yet a Git repository, initialize it and connect your GitHub remote first:

```powershell
git init
git branch -M main
git remote add origin https://github.com/<your-user-or-org>/<your-repo>.git
```

Make sure these deploy-critical files are committed:

```powershell
git status --short
git add .dockerignore .gitignore Dockerfile start.sh app/services/data_refresh.py docs/deployment-render.md README.md
git add data/bootstrap/worldcup.duckdb frontend/public/earth_at_night.jpg frontend/public/logo.png
git commit -m "Prepare Render deployment"
git push
```

`frontend/dist` should not be committed; Docker builds it.

### 4. Create the Render Blueprint

1. Open [Render Dashboard](https://dashboard.render.com).
2. Click **New**.
3. Choose **Blueprint**.
4. Connect the GitHub repository.
5. Select the repository containing `render.yaml`.
6. Render should detect one service: `worldcup-travel-atlas`.
7. Click **Apply**.

Render will use:

- Runtime: Docker
- Dockerfile: `./Dockerfile`
- Health check path: `/healthz`
- Plan: Free
- Auto deploy: Enabled

### 5. Wait for the first deploy

Render will:

1. Build the frontend in the Node stage.
2. Build the Python/FastAPI runtime image.
3. Copy `data/bootstrap/worldcup.duckdb` into the image.
4. Start `uvicorn` through `start.sh`.
5. Copy the baseline database to `/tmp/worldcup.duckdb`.
6. Run the ingest and dbt refresh because `REFRESH_DATA_ON_START=true`.
7. Probe `/healthz`.

The first deploy can take several minutes due to `npm ci`, `pip install`, and the startup data refresh.

### 6. Verify the live deployment

```bash
curl https://<your-service>.onrender.com/healthz
```

Expected response (shape):

```json
{
  "status": "ok",
  "database_available": true,
  "data_timestamp": "2026",
  "version": "1.0.0"
}
```

Browse the app root URL to load the SPA. Test an API call:

```bash
curl https://<your-service>.onrender.com/api/v1/meta
```

Also verify in the browser:

- The 3D globe loads with the night-earth texture.
- The logo appears and links to `https://www.datafoundry.ch`.
- 2026 loads by default.
- The 2026 team chart does not include placeholder teams like `L101`, `L102`, `W101`, or `W102`.

## Blueprint configuration (`render.yaml`)

```yaml
services:
  - type: web
    name: worldcup-travel-atlas
    runtime: docker
    plan: free
    autoDeploy: true
    healthCheckPath: /healthz
    dockerfilePath: ./Dockerfile
```

### Environment variables

| Variable | Render default | Purpose |
|----------|----------------|---------|
| `APP_ENV` | `production` | Enable static SPA serving |
| `OPENFOOTBALL_GITHUB_REF` | `master` | Git ref for tournament JSON |
| `REFRESH_DATA_ON_START` | `true` | Run full ingest + dbt on startup |
| `DATA_FRESHNESS_WARNING_HOURS` | `36` | Stale data threshold for UI |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `DUCKDB_PATH` | `/tmp/worldcup.duckdb` | Writable runtime database |
| `DUCKDB_BASELINE_PATH` | `/app/data/bootstrap/worldcup.duckdb` | Cold-start baseline |
| `PORT` | `10000` (set by Render) | uvicorn listen port |

Render injects `PORT` automatically. `start.sh` binds `0.0.0.0:$PORT`.

### Dockerfile highlights

| Stage | Base | Output |
|-------|------|--------|
| `frontend-build` | `node:22-alpine` | `frontend/dist` |
| `runtime` | `python:3.12-slim` | API + static files + baseline DB |

Notable runtime settings:
- `truststore` installed for SSL (same as local Windows fix, also useful in slim images)
- `REFRESH_DATA_ON_START=false` in Dockerfile ENV — **overridden** by `render.yaml` to `true`
- Non-root user `appuser` (uid 10001)
- Built-in Docker `HEALTHCHECK` on `/healthz`

## Startup behavior

On each container start:

1. **Baseline copy** — If `/tmp/worldcup.duckdb` does not exist, copy from `/app/data/bootstrap/worldcup.duckdb`
2. **Optional refresh** — When `REFRESH_DATA_ON_START=true`:
   - Download all 23 tournament JSON files from OpenFootball
   - Write `matches.parquet` and ingestion manifest
   - Run venue coverage report
   - Execute `dbt build` into a temp database
   - Atomically replace `/tmp/worldcup.duckdb`
3. **Serve** — uvicorn starts; API reads DuckDB read-only

If refresh fails, the previous database (or baseline) is retained.

## Scheduled refresh

`.github/workflows/refresh-render.yml` triggers a redeploy:

- **Cron:** `0 6 * * *` (daily 06:00 UTC)
- **Manual:** `workflow_dispatch`
- **Requires:** GitHub secret `RENDER_DEPLOY_HOOK_URL`

### Configure deploy hook

1. In Render: service → **Settings** → **Deploy Hook** → copy URL
2. In GitHub: repo → **Settings** → **Secrets** → add `RENDER_DEPLOY_HOOK_URL`
3. Workflow POSTs to the hook, triggering a new deploy (and thus `REFRESH_DATA_ON_START`)

Without the secret, the workflow fails with a clear error message.

## Local Docker (reference)

```bash
make docker-build
make docker-run    # maps port 10000
curl http://127.0.0.1:10000/healthz
```

Local Docker was verified with both `REFRESH_DATA_ON_START=false` (baseline startup) and `REFRESH_DATA_ON_START=true` (Render-style startup refresh).

## CI vs Render

| Aspect | GitHub Actions CI | Render production |
|--------|-------------------|-------------------|
| Ingestion | Fixture JSON only (`--local-only`) | Full OpenFootball download |
| dbt | Fixture parquet | Live 1,069-match parquet |
| `REFRESH_DATA_ON_START` | N/A | `true` |
| DuckDB path | `data/worldcup.duckdb` | `/tmp/worldcup.duckdb` |

## Troubleshooting

### Health check fails / `status: degraded`

- Container started before DuckDB was initialized
- Check Render logs for `initialize_runtime` or `dbt build` errors
- Verify baseline exists: `/app/data/bootstrap/worldcup.duckdb`

### Slow cold starts

- `REFRESH_DATA_ON_START=true` runs full pipeline synchronously before accepting traffic
- Free-tier instances also spin down after inactivity (30–60 s extra wake time)
- Consider setting `REFRESH_DATA_ON_START=false` and relying on deploy hooks only

### dbt build failure in production

- Check logs for `dbt build failed` stderr tail
- Common causes: OpenFootball download failure, disk space on `/tmp`
- Failed refresh keeps existing DB — app may serve stale but functional data

### Frontend 404 in production

- Ensure `APP_ENV=production` (serves `frontend/dist`)
- Docker build stage must complete `npm run build`
- SPA fallback returns `index.html` for non-API paths

### SSL / download errors

- `truststore` is bundled in the Docker image
- Verify outbound HTTPS to `raw.githubusercontent.com` is allowed on Render

## Operations checklist

- [ ] `/healthz` returns `status: ok`
- [ ] `/api/v1/meta` shows `coordinate_coverage.coverage_pct: 100`
- [ ] `/api/v1/tournaments` lists 23 editions
- [ ] Deploy hook secret configured for daily refresh
- [ ] Monitor Render logs after OpenFootball data updates

## Related documents

- [architecture.md](architecture.md) — runtime lifecycle
- [methodology.md](methodology.md) — what the data represents
- [venue-enrichment.md](venue-enrichment.md) — updating coordinates after deploy
