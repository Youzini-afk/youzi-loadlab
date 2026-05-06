# NashiYard Polling System Stress Scenario

## Purpose

The `nashiyard-polling-system` scenario measures how repeated polling-style API calls affect NashiYard while optional foreground chat traffic continues. It is useful for testing dashboard refresh behavior, background maintenance pressure, and operator workflows that repeatedly inspect channels, tokens, and usage data.

The current runner implements Locust tasks for polling requests and an optional foreground `/v1/chat/completions` request. It does not yet authenticate differently per polling endpoint, discover endpoint availability, or perform NashiYard admin setup automatically.

## Implemented Runner Pieces

| Piece | Location | Status |
| --- | --- | --- |
| Scenario registry ID | `apps/api/youziloadlab_api/services/scenario_registry.py` | Implemented as `nashiyard-polling-system`. |
| Config schema | `runner/youziloadlab_runner/scenarios/config_schemas.py` | Implemented as `POLLING_SCHEMA`. |
| Polling task planner | `runner/youziloadlab_runner/scenarios/nashiyard_polling_system.py` | Implemented by `build_polling_tasks()`. |
| Foreground chat ratio helper | `runner/youziloadlab_runner/scenarios/nashiyard_polling_system.py` | Implemented by `should_run_foreground_chat()`. |
| Locust traffic class | `runner/youziloadlab_runner/scenarios/nashiyard_polling_system.py` | Implemented as `NashiYardPollingUser`. |
| Endpoint-specific auth headers/cookies | `runner/youziloadlab_runner/scenarios/nashiyard_polling_system.py` | Implemented through `--polling-auth-header` / `--polling-cookie` and corresponding env vars. |

## Default Polling Tasks

| Name | Method | Path | Default Interval |
| --- | --- | --- | ---: |
| `channel_list` | `GET` | `/api/channel/` | 5s |
| `token_list` | `GET` | `/api/token/` | 10s |
| `usage` | `GET` | `/api/log/self` | 15s |

The helper `build_polling_tasks()` exposes these defaults for configuration and tests. The current Locust class uses weighted tasks rather than strict interval scheduling, so treat the interval values as configuration intent for the WebUI/API rather than an exact timing guarantee in Locust execution.

## Mixed Foreground Chat

When foreground chat is enabled, the scenario posts to `/v1/chat/completions` with an OpenAI-compatible request body. The default foreground chat ratio is `0.3`, implemented by `should_run_foreground_chat()`.

Default foreground chat options used by the Locust class are:

| Option | Default |
| --- | --- |
| Token option | `--token`, default empty string |
| Model option | `--model`, default `gpt-4o-mini` |
| Prompt option | `--polling-prompt`, default `Short health check response.` |
| Max tokens option | `--polling-max-tokens`, default `64` |
| Temperature option | `--polling-temperature`, default `0.2` |
| Foreground ratio option | `--foreground-chat-ratio`, default `0.3` |

The polling runner registers its own polling options in addition to the shared OpenAI chat options. Use `--polling-auth-header` for bearer-style admin/user tokens, `--polling-cookie` for session cookies, and `--foreground-chat-ratio` to control mixed foreground traffic.

## Required Inputs

Prepare these values before running the scenario:

- NashiYard base URL.
- Credentials or session behavior appropriate for `/api/channel/`, `/api/token/`, and `/api/log/self` in the target environment.
- A safe API token and model if foreground chat is enabled.
- Operator-defined thresholds for admin endpoint latency, foreground chat p95 latency, and acceptable failure rate.

Do not run this first against a production admin account. Use a staging or isolated NashiYard instance until the endpoint mix and authentication behavior are understood.

## Local Locust Command

Run from the repository root. Replace values with a safe target and token.

```powershell
py -3.13 -m locust `
  -f runner/youziloadlab_runner/scenarios/nashiyard_polling_system.py `
  --headless `
  --host https://nashiyard.example.com `
  --users 10 `
  --spawn-rate 2 `
  --run-time 5m `
  --token sk-test-user-token `
  --model gpt-4o-mini
```

If the target admin endpoints require browser-session cookies or admin tokens, provide them through `--polling-cookie` or `--polling-auth-header`. Otherwise, repeated `401` or `403` responses only prove that the endpoints are protected.

## Suggested Load Profiles

Start small and increase pressure only after the target behaves as expected:

| Pass | Runtime | Users | Spawn Rate | Goal |
| --- | ---: | ---: | ---: | --- |
| Smoke | 60s | 1 | 1 | Confirm auth and endpoint availability. |
| Baseline | 5m | 5 | 1 | Capture normal polling latency and error mix. |
| Mixed | 10m | 20 | 2 | Observe dashboard-style polling plus foreground chat. |
| Peak | 10m | 50 | 5 | Find admin endpoint saturation or gateway contention. |
| Recovery | 5m | 5 | 1 | Confirm latency and failures return to baseline. |

## What to Watch

Separate polling and chat outcomes in the report:

- `Polling GET /api/channel/` latency and failure rate.
- `Polling GET /api/token/` latency and failure rate.
- `Polling GET /api/log/self` latency and failure rate.
- `Polling foreground chat` p95/p99 latency and failure rate.
- `401` and `403` responses caused by missing admin/session auth.
- `429` rate limits caused by repeated polling.
- `5xx` responses or panic traces in NashiYard logs.
- Any response body or log excerpt that contains secrets, tokens, or provider keys.

## Success Criteria

- Polling endpoints stay responsive at the agreed user count and runtime.
- Foreground chat p95 latency remains within the operator-defined threshold.
- Polling failures are reported separately from foreground chat failures.
- Repeated admin/user observation calls do not leak secrets or trigger panics.
- Recovery pass returns close to baseline latency and error rate.

## Cleanup Checklist

After the run:

1. Revoke test tokens used for foreground chat if they are not needed again.
2. Remove any temporary admin/session credentials from local environment variables.
3. Archive the endpoint mix, users, spawn rate, runtime, and foreground ratio.
4. Compare polling-only and mixed-traffic runs before changing production polling intervals.
