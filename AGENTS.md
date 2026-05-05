# AGENTS.md - YouziLoadLab

## Project Mission

Build a polished Zeabur-deployable load-testing WebUI for NashiYard and OpenAI-compatible APIs.

## Architecture Rules

- Product API code lives in `apps/api/youziloadlab_api`.
- Load execution and scenario logic lives in `runner/youziloadlab_runner`.
- Web UI code lives in `apps/web/src`.
- Do not put NashiYard-specific setup logic in the WebUI.
- Do not put Locust user classes inside FastAPI modules.
- Do not log plaintext secrets.

## Testing

Run Python tests:

```powershell
pytest apps/api/tests runner/tests -q
```

Run Web tests:

```powershell
pnpm --filter @youziloadlab/web test
```
