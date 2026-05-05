# Zeabur Deployment

YouziLoadLab deploys as a single Dockerfile-based Zeabur service. The image builds the React WebUI, installs the FastAPI/Locust runtime, and starts Uvicorn on port `8000`.

## Required Environment Variables

- `APP_ENV=production`
- `APP_SECRET_KEY=<32+ character secret>`
- `ADMIN_PASSWORD=<operator password>`
- `DATABASE_URL=sqlite:////data/youziloadlab.db`
- `DATA_DIR=/data`
- `RUNNER_WORKDIR=/data/runs`
- `MAX_CONCURRENT_RUNS=1`
- `MAX_USERS_PER_RUN=200`

## Volume

Mount a persistent volume at `/data`.

The SQLite database and run artifacts should live under this volume so redeploys do not delete run history.

## Health Check

After deployment, open:

```text
https://<your-zeabur-domain>/api/health
```

Expected response contains:

```json
{"status":"ok"}
```

## WebUI

The React WebUI is served by the same FastAPI service. Open:

```text
https://<your-zeabur-domain>/
```

API routes remain under `/api/*`, and the single-page app fallback serves `index.html` for WebUI client-side routes such as `/runs/<run-id>`.

## Local Docker Validation

Build the image:

```powershell
docker build -t youziloadlab .
```

Run with docker compose:

```powershell
docker compose up --build
```

Then verify:

```text
http://localhost:8000/api/health
http://localhost:8000/
```

## Implementation Notes

- The Dockerfile copies the existing `pnpm-lock.yaml` and uses `pnpm install --frozen-lockfile` so container builds match local WebUI dependency resolution.
- The WebUI build output is copied to `apps/api/youziloadlab_api/static`.
- FastAPI serves the copied WebUI from the same process when `static/index.html` exists, while `/api/*` routes keep priority over the SPA fallback.
