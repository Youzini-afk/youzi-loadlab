# YouziLoadLab

YouziLoadLab is an independently deployable WebUI load-testing platform for NashiYard and OpenAI-compatible API gateways.

## Goals

- Provide a polished WebUI for configuring targets, secrets, scenarios, runs, and reports.
- Use Locust as the execution engine instead of rebuilding concurrency and latency statistics from scratch.
- Support NashiYard Fireworks channel pressure testing in V1.
- Support polling-system pressure tests as a first-class scenario family.
- Deploy as a single Zeabur service with persistent storage mounted at `/data`.

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
pnpm install
pytest apps/api/tests runner/tests -q
uvicorn youziloadlab_api.main:app --app-dir apps/api --reload
```

## Validation

See `docs/validation.md` for the full pre-release validation checklist.
