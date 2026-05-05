# Scenario Authoring

YouziLoadLab scenarios live in the runner package and are exposed to the API/WebUI through the scenario registry. Keep scenario-specific load behavior in `runner/youziloadlab_runner`; keep FastAPI focused on orchestration, persistence, and reports.

## Current Scenario IDs

| Scenario ID | Runner module | Primary purpose |
| --- | --- | --- |
| `openai-chat-load` | `runner/youziloadlab_runner/scenarios/openai_chat_load.py` | Generic OpenAI-compatible `/v1/chat/completions` pressure traffic. |
| `nashiyard-fireworks-channel` | `runner/youziloadlab_runner/scenarios/nashiyard_fireworks_channel.py` | Fireworks channel chat traffic plus helper defaults for phased runs. |
| `nashiyard-polling-system` | `runner/youziloadlab_runner/scenarios/nashiyard_polling_system.py` | Polling-style NashiYard admin/user endpoint traffic with optional foreground chat. |
| `smoke-check` | `runner/youziloadlab_runner/scenarios/smoke_check.py` | Preflight checklist metadata for health, models, chat, and sanitization checks. |

## Scenario Anatomy

A scenario should have these pieces:

1. A JSON-schema style config entry in `runner/youziloadlab_runner/scenarios/config_schemas.py` when the WebUI/API needs structured configuration.
2. Small, unit-testable helper functions in `runner/youziloadlab_runner/scenarios/<scenario_name>.py`.
3. A Locust `HttpUser` class when the scenario generates load traffic.
4. API registry metadata in `apps/api/youziloadlab_api/services/scenario_registry.py` so the WebUI can list it.
5. Focused tests in `runner/tests` and, when registry behavior changes, `apps/api/tests`.

## Authoring Rules

- Put NashiYard-specific setup, cleanup, and request planning in runner modules, not in `apps/web`.
- Put shared OpenAI-compatible payload construction in `runner/youziloadlab_runner/payloads.py`.
- Keep secret handling out of logs, reports, and Locust request names; use IDs or redacted labels instead.
- Add tests for helper functions before adding or changing Locust user behavior.
- Prefer small helpers over large scenario classes; helpers are easier to test without running Locust.
- Do not claim a scenario performs admin setup or cleanup unless the code actually calls the NashiYard admin adapter.

## Adding a New Scenario

1. Create a failing test in `runner/tests/test_<scenario_name>.py`.
2. Add helper functions and, if needed, a Locust `HttpUser` in `runner/youziloadlab_runner/scenarios/<scenario_name>.py`.
3. Add a schema in `runner/youziloadlab_runner/scenarios/config_schemas.py` if the scenario has user-configurable fields.
4. Add registry metadata in `apps/api/youziloadlab_api/services/scenario_registry.py` using a stable kebab-case scenario ID.
5. Run the Python checks:

```powershell
py -3.13 -m pytest runner/tests apps/api/tests -q
py -3.13 -m ruff check apps/api runner
py -3.13 -m mypy apps/api runner
```

## Local Locust Smoke Commands

Run these from the repository root after installing project dependencies. Replace the host, token, and model with a safe test target.

```powershell
py -3.13 -m locust `
  -f runner/youziloadlab_runner/scenarios/openai_chat_load.py `
  --headless `
  --host http://localhost:3000 `
  --users 1 `
  --spawn-rate 1 `
  --run-time 30s `
  --token sk-test `
  --model gpt-4o-mini
```

For WebUI-managed runs, create a target, create secrets, choose a scenario from `/api/scenarios`, then create a run through `/api/runs` or the dashboard. The current implementation starts Locust as a local process; large distributed Locust clusters are outside the first implementation.

## Documentation Checklist

Every operator guide should state:

- What the scenario measures.
- Which endpoints it calls.
- Which secrets and tokens are required.
- What defaults are encoded in code.
- Which abilities are currently implemented and which actions remain manual.
- How to run the scenario safely against a non-production target first.
- How to interpret success criteria without exposing plaintext secrets.
