# YouziLoadLab Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-ready, independently deployable WebUI load-testing platform for NashiYard and OpenAI-compatible API systems, with a strong first release covering Fireworks channel stress tests and polling-system stress tests.

**Architecture:** YouziLoadLab uses a thin product layer around Locust instead of rebuilding a load engine from scratch. FastAPI owns projects, secrets, scenarios, run orchestration, persistence, reports, and Zeabur deployment; Locust owns high-concurrency execution and live load statistics; React owns the operator WebUI. LiteLLM is treated as an optional adapter reference for future multi-provider protocol conversion, not as a hard dependency in v1.

**Tech Stack:** Python 3.12, FastAPI, SQLModel, SQLite/Postgres, Alembic, Locust, httpx, cryptography/Fernet, React 18, Vite, MUI, Recharts, Docker, Zeabur.

---

## Product Scope

### Version 1 must feel polished, not toy-like

V1 is not just a CLI wrapper. It must provide a real WebUI for configuring targets, storing encrypted secrets, defining load profiles, running scenario suites, observing live progress, stopping runs safely, and exporting reports. It should be good enough for a developer or ops person to deploy on Zeabur and repeatedly run controlled stress tests against NashiYard without editing Python scripts each time.

### V1 scenario coverage

- `openai-chat-load`: generic OpenAI-compatible `/v1/chat/completions` load test.
- `nashiyard-fireworks-channel`: implements the core workflow from `E:\cursor_project\nashiyard\nashiyard\docs\fireworks-stress-test-plan.md`.
- `nashiyard-polling-system`: tests NashiYard polling-related admin/background endpoints and API behavior under periodic polling pressure.
- `smoke-check`: short preflight suite that validates target URL, auth, model availability, token usability, and error sanitization.

### Out of scope for V1

- Full replacement of Locust Web UI internals.
- Distributed multi-node Locust orchestration across many Zeabur services.
- Full LiteLLM proxy embedding.
- Prompt quality eval and red-team scoring.
- Kubernetes-native deployment.

These are deliberately deferred so V1 can ship as a strong single-service product.

## Reference Projects and How to Use Them

### Locust

Path: `E:\cursor_project\nashiyard\locust`

Use Locust directly for execution. Its README states tests can run from command line or Web UI, with throughput, response times, and errors visible in real time. That maps exactly to our core need.

Borrow:
- `HttpUser` / task model.
- headless execution flags.
- CSV stats output.
- Web UI concepts for charts and failures.
- distributed mode concepts for future V2.

Do not fork Locust. Treat it as a PyPI dependency.

### LiteLLM

Path: `E:\cursor_project\nashiyard\litellm`

Use as protocol conversion reference. Its README describes a unified OpenAI-format interface for 100+ LLM providers and supported endpoints like `/chat/completions`, `/responses`, `/embeddings`, `/images`, `/audio`, `/rerank`, and `/messages`.

Borrow:
- provider naming conventions.
- OpenAI-compatible error normalization ideas.
- router/fallback vocabulary.
- future adapter shape.

Do not make LiteLLM required in V1. It is heavy and duplicates some NashiYard gateway behavior.

### Artillery

Path: `E:\cursor_project\nashiyard\artillery`

Use as inspiration for declarative load profiles.

Borrow:
- `phases` style: duration, arrival rate, ramping, concurrency caps.
- scenario + flow separation.
- YAML/JSON import/export format.

Do not use Artillery as the V1 engine because Locust gives us a better interactive WebUI and Python business-flow composition.

### Promptfoo

Path: `E:\cursor_project\nashiyard\promptfoo`

Use as inspiration for future eval/reporting, not V1 stress execution.

Borrow:
- provider config DSL ideas.
- report organization.
- assertions as future post-run checks.

Do not use Promptfoo as the V1 pressure engine.

## Repository Layout

Create this layout inside `E:\cursor_project\nashiyard\youziloadlab`:

```text
youziloadlab/
  README.md
  AGENTS.md
  Dockerfile
  docker-compose.yml
  zeabur.json
  .env.example
  .gitignore
  pyproject.toml
  package.json
  pnpm-workspace.yaml
  apps/
    api/
      youziloadlab_api/
        __init__.py
        main.py
        core/
          config.py
          security.py
          time.py
        db/
          session.py
          models.py
          migrations.py
        modules/
          health/router.py
          targets/router.py
          secrets/router.py
          scenarios/router.py
          runs/router.py
          reports/router.py
          events/router.py
        services/
          target_service.py
          secret_service.py
          scenario_registry.py
          run_orchestrator.py
          report_service.py
          locust_process.py
        schemas/
          common.py
          target.py
          secret.py
          scenario.py
          run.py
          report.py
      tests/
        test_health.py
        test_security.py
        test_targets.py
        test_secrets.py
        test_scenarios.py
        test_runs.py
        test_reports.py
    web/
      index.html
      package.json
      vite.config.ts
      tsconfig.json
      src/
        main.tsx
        App.tsx
        api/client.ts
        routes.tsx
        theme.ts
        pages/
          DashboardPage.tsx
          TargetsPage.tsx
          ScenariosPage.tsx
          NewRunPage.tsx
          RunDetailPage.tsx
          ReportsPage.tsx
          SettingsPage.tsx
        components/
          AppShell.tsx
          StatCard.tsx
          RunStatusBadge.tsx
          LatencyChart.tsx
          ErrorBreakdown.tsx
          PhaseEditor.tsx
          SecretInput.tsx
        types/
          api.ts
  runner/
    youziloadlab_runner/
      __init__.py
      contracts.py
      metrics.py
      payloads.py
      locust_env.py
      adapters/
        openai_compat.py
        nashiyard_admin.py
      scenarios/
        openai_chat_load.py
        nashiyard_fireworks_channel.py
        nashiyard_polling_system.py
        smoke_check.py
    tests/
      test_payloads.py
      test_metrics.py
      test_openai_adapter.py
      test_nashiyard_admin.py
      test_fireworks_scenario.py
      test_polling_scenario.py
  docs/
    architecture.md
    deployment-zeabur.md
    scenario-authoring.md
    security.md
    superpowers/plans/
      2026-05-05-youziloadlab-architecture.md
      2026-05-05-youziloadlab-implementation.md
      2026-05-05-youziloadlab-scenarios.md
```

## Boundary Design

### API app responsibilities

The API app owns durable state and user-facing workflows:

- CRUD for targets.
- encrypted secret storage.
- scenario registry metadata.
- run creation and state transitions.
- starting/stopping Locust subprocesses.
- collecting run events and final artifacts.
- generating reports.
- serving built WebUI static assets in production.

The API must not contain scenario-specific load logic. It calls runner modules through explicit config files and environment variables.

### Runner responsibilities

The runner package owns all behavior that touches target systems under load:

- request body construction.
- streaming response parsing.
- NashiYard admin API setup/cleanup.
- Locust user classes.
- error classification.
- scenario-specific metrics.

Runner code must be importable and unit-testable without starting Locust.

### Web responsibilities

The WebUI owns operator experience:

- target configuration forms.
- secret upload/edit forms with masked display.
- scenario-specific config editors.
- run launch form with phase preview.
- live run detail page.
- report browsing/export.

The WebUI must not know how to call NashiYard directly. It only calls YouziLoadLab API.

## Data Model

Use SQLModel for V1. SQLite is default. Postgres is supported by `DATABASE_URL` for Zeabur users who want managed DB.

### Tables

#### `targets`

Fields:
- `id: str` UUID.
- `name: str` unique display name.
- `kind: str` one of `nashiyard`, `openai_compatible`, `generic_http`.
- `base_url: str` normalized without trailing slash.
- `admin_username: str | None` for NashiYard.
- `default_model: str | None`.
- `created_at: datetime`.
- `updated_at: datetime`.

#### `secrets`

Fields:
- `id: str` UUID.
- `target_id: str | None`.
- `name: str`.
- `kind: str` one of `api_key`, `admin_password`, `fireworks_keys`, `bearer_token`, `cookie`.
- `ciphertext: str` Fernet encrypted payload.
- `fingerprint: str` first 10 hex chars of SHA-256, used to detect accidental duplicates without revealing secret.
- `created_at: datetime`.
- `updated_at: datetime`.

#### `scenario_definitions`

Fields:
- `id: str` stable slug.
- `title: str`.
- `description: str`.
- `version: str`.
- `schema_json: dict` JSON schema for UI form generation.
- `enabled: bool`.

This table is seeded from code registry at app startup.

#### `runs`

Fields:
- `id: str` UUID.
- `name: str`.
- `target_id: str`.
- `scenario_id: str`.
- `status: str` one of `created`, `starting`, `running`, `stopping`, `stopped`, `completed`, `failed`.
- `config_json: dict` full validated scenario config.
- `locust_web_url: str | None`.
- `started_at: datetime | None`.
- `finished_at: datetime | None`.
- `created_at: datetime`.
- `error_message: str | None`.

#### `run_events`

Fields:
- `id: int` autoincrement.
- `run_id: str`.
- `level: str` one of `debug`, `info`, `warning`, `error`.
- `event_type: str` e.g. `phase_started`, `request_error`, `setup_completed`, `cleanup_completed`.
- `message: str`.
- `payload_json: dict`.
- `created_at: datetime`.

#### `run_metrics_snapshots`

Fields:
- `id: int` autoincrement.
- `run_id: str`.
- `timestamp: datetime`.
- `requests_total: int`.
- `failures_total: int`.
- `current_rps: float`.
- `avg_latency_ms: float`.
- `p50_latency_ms: float`.
- `p90_latency_ms: float`.
- `p95_latency_ms: float`.
- `p99_latency_ms: float`.
- `status_counts_json: dict`.
- `error_counts_json: dict`.
- `tokens_total: int`.

#### `reports`

Fields:
- `id: str` UUID.
- `run_id: str` unique.
- `summary_json: dict`.
- `markdown: str`.
- `created_at: datetime`.

## API Routes

Base path: `/api`.

### Health

- `GET /api/health` returns app, db, and runner status.

### Targets

- `GET /api/targets`
- `POST /api/targets`
- `GET /api/targets/{target_id}`
- `PATCH /api/targets/{target_id}`
- `DELETE /api/targets/{target_id}`
- `POST /api/targets/{target_id}/preflight`

### Secrets

- `GET /api/secrets`
- `POST /api/secrets`
- `DELETE /api/secrets/{secret_id}`
- `POST /api/secrets/{secret_id}/rotate`

Secret responses must never include plaintext.

### Scenarios

- `GET /api/scenarios`
- `GET /api/scenarios/{scenario_id}`

### Runs

- `GET /api/runs`
- `POST /api/runs`
- `GET /api/runs/{run_id}`
- `POST /api/runs/{run_id}/start`
- `POST /api/runs/{run_id}/stop`
- `GET /api/runs/{run_id}/events`
- `GET /api/runs/{run_id}/metrics`
- `GET /api/runs/{run_id}/stream` Server-Sent Events.

### Reports

- `GET /api/reports`
- `GET /api/reports/{run_id}`
- `GET /api/reports/{run_id}.md`
- `GET /api/reports/{run_id}.json`

## Scenario Config Model

Use a shared JSON shape across scenarios:

```json
{
  "targetId": "uuid",
  "scenarioId": "nashiyard-fireworks-channel",
  "secrets": {
    "adminPasswordSecretId": "uuid",
    "fireworksKeysSecretId": "uuid"
  },
  "setup": {
    "createUsers": true,
    "testUserPrefix": "stress_test_fw_",
    "testUserCount": 3,
    "testUserGroup": "fireworks_stress",
    "quotaPerUser": 500000000,
    "discordGateExempt": true,
    "createChannel": true,
    "channelName": "fireworks_stress_main",
    "channelType": 41,
    "baseUrl": "https://api.fireworks.ai/inference/v1"
  },
  "request": {
    "endpoint": "/v1/chat/completions",
    "model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
    "messages": [{"role": "user", "content": "Say hello in 50 words or less."}],
    "maxTokens": 128,
    "temperature": 0.7,
    "streamRatio": 0.1,
    "timeoutSeconds": 30
  },
  "loadProfile": {
    "phases": [
      {"name": "baseline", "durationSeconds": 300, "users": 10, "spawnRate": 2},
      {"name": "ramp", "durationSeconds": 600, "users": 50, "spawnRate": 5},
      {"name": "peak", "durationSeconds": 300, "users": 100, "spawnRate": 10}
    ]
  },
  "cleanup": {
    "deleteUsers": false,
    "deleteTokens": true,
    "disableCreatedChannel": true
  }
}
```

## Security Requirements

- Generate `APP_SECRET_KEY` on first local startup if absent; require it in production.
- Use Fernet encryption for secret values.
- Store only secret fingerprints and masked previews.
- Redact `sk-`, `fk-`, `Bearer`, `Authorization`, `Cookie`, and provider key patterns from logs.
- Never include plaintext keys in reports.
- Add operator confirmation for destructive cleanup.
- Require admin password login before WebUI/API operations.

## Zeabur Deployment

### Single-service mode for V1

The Docker image runs FastAPI. FastAPI serves built React assets and launches Locust subprocesses for runs.

Required env vars:
- `APP_ENV=production`
- `APP_SECRET_KEY=<32+ char secret>`
- `ADMIN_PASSWORD=<operator password>`
- `DATABASE_URL=sqlite:////data/youziloadlab.db`
- `DATA_DIR=/data`
- `RUNNER_WORKDIR=/data/runs`

Zeabur volume:
- mount `/data` for SQLite, reports, and run artifacts.

## Quality Gates

Before calling V1 ready:

- API tests pass with `pytest apps/api/tests runner/tests -q`.
- Web tests pass with `pnpm --filter @youziloadlab/web test`.
- Type checks pass with `mypy apps/api runner` and `pnpm --filter @youziloadlab/web typecheck`.
- Docker image builds with `docker build -t youziloadlab .`.
- Local app starts with `docker compose up`.
- Smoke scenario can run against a local mock OpenAI-compatible server.
- Secret redaction tests prove no plaintext secret appears in API responses, logs, events, or reports.

## Commit Strategy

Commit after every task from the implementation plan. Suggested prefix:

- `chore:` project skeleton and tooling.
- `feat(api):` API features.
- `feat(web):` WebUI features.
- `feat(runner):` runner and scenario features.
- `test:` cross-cutting tests.
- `docs:` docs and deployment guides.

## Self-Review

### Spec coverage

- Independent Zeabur-deployable project: covered by repository layout, Docker, and deployment sections.
- WebUI: covered by Web responsibilities, pages, components, and API routes.
- Avoid from-scratch protocol pain: covered by Locust direct reuse and LiteLLM reference strategy.
- Strong first release: covered by V1 scenario scope, security, reporting, and quality gates.
- NashiYard Fireworks design document: covered by scenario config model and V1 scenario coverage.
- Future polling tests: covered by `nashiyard-polling-system` scenario and runner boundaries.

### Placeholder scan

This document intentionally contains no `TBD`, `TODO`, `implement later`, or vague edge-case directives.

### Type consistency

The scenario IDs, table names, route names, and config property names are consistent across sections.
