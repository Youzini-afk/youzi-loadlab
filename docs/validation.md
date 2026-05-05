# Validation Checklist

Run these commands before marking V1 implementation complete.

## Commands

```powershell
py -3.13 -m pytest apps/api/tests runner/tests -q
py -3.13 -m ruff check apps/api runner
py -3.13 -m mypy apps/api runner
pnpm --filter @youziloadlab/web typecheck
pnpm --filter @youziloadlab/web build
docker build -t youziloadlab .
```

## Expected Results

- `pytest` passes for API and runner tests.
- `ruff` reports no lint errors.
- `mypy` reports no type errors.
- TypeScript typecheck passes for the WebUI.
- Vite builds the WebUI successfully.
- Docker image builds successfully.

## Docker Environment Note

If Docker Desktop is not running or the Linux engine pipe is unavailable on Windows, the Docker build can fail before reading the project `Dockerfile`. Treat that as a local environment blocker, start Docker Desktop, and rerun:

```powershell
docker build -t youziloadlab .
```
