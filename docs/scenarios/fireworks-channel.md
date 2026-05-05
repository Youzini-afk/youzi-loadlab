# NashiYard Fireworks Channel Stress Scenario

## Purpose

The `nashiyard-fireworks-channel` scenario is the first NashiYard-specific pressure suite. It targets OpenAI-compatible chat traffic routed through a NashiYard Fireworks channel and records whether the gateway remains stable during smoke, baseline, ramp, peak, fault-injection, and recovery phases.

The current runner implements the chat load generator and phase/user-name planning helpers. Operator-driven or API-driven admin setup is still required for creating users, tokens, quotas, and channels before running the load test.

## Implemented Runner Pieces

| Piece | Location | Status |
| --- | --- | --- |
| Scenario registry ID | `apps/api/youziloadlab_api/services/scenario_registry.py` | Implemented as `nashiyard-fireworks-channel`. |
| Config schema | `runner/youziloadlab_runner/scenarios/config_schemas.py` | Implemented as `FIREWORKS_SCHEMA`. |
| Phase defaults | `runner/youziloadlab_runner/scenarios/nashiyard_fireworks_channel.py` | Implemented by `default_fireworks_phases()`. |
| Test username planner | `runner/youziloadlab_runner/scenarios/nashiyard_fireworks_channel.py` | Implemented by `build_test_usernames()`. |
| Locust traffic class | `runner/youziloadlab_runner/scenarios/nashiyard_fireworks_channel.py` | Implemented as `NashiYardFireworksUser`. |
| Automatic admin setup/cleanup | N/A | Not yet implemented in this scenario runner. |

## Defaults

| Field | Default |
| --- | --- |
| Test user prefix | `stress_test_fw_` |
| Test user count | `3` |
| Test user group | `fireworks_stress` |
| Quota per user | `500000000` |
| Discord gate exempt | `true` |
| Create channel flag | `true` |
| Channel name | `fireworks_stress_main` |
| Channel type | `41` |
| Fireworks base URL | `https://api.fireworks.ai/inference/v1` |
| Model | `accounts/fireworks/models/llama-v3p1-8b-instruct` |
| Prompt | `Say hello in 50 words or less.` |
| Max tokens | `128` |
| Temperature | `0.7` |
| Stream ratio | `0.1` |
| Timeout seconds | `30` |

## Default Phases

| Phase | Duration | Users | Spawn Rate |
| --- | ---: | ---: | ---: |
| `smoke` | 60s | 5 | 2 |
| `baseline` | 300s | 10 | 2 |
| `ramp` | 600s | 50 | 5 |
| `peak` | 300s | 100 | 10 |
| `fault_injection` | 600s | 30 | 3 |
| `recovery` | 300s | 20 | 2 |

These values are returned by `default_fireworks_phases()`. The current Locust command must be run once per desired phase or launched by the API run orchestrator with equivalent users, spawn rate, and runtime settings.

## Required Inputs

Prepare these values before running the scenario:

- NashiYard base URL, for example `https://gateway.example.com`.
- A NashiYard API token that is safe to use for pressure testing.
- A Fireworks-backed NashiYard channel mapped to the model under test.
- A test model name, usually `accounts/fireworks/models/llama-v3p1-8b-instruct`.
- A decision on whether streaming should be included through `--stream-ratio`.

Do not use production user tokens or production-only channels for the first run. Start with a smoke phase against an isolated test user and test channel.

## Manual Setup Checklist

The current code includes a NashiYard admin adapter, but this scenario runner does not yet execute full Fireworks setup/cleanup automatically. Until that orchestration is wired in, perform setup manually or through a separate controlled script:

1. Create isolated test users using the `stress_test_fw_` prefix.
2. Put those users in the `fireworks_stress` group if group-based routing is required.
3. Set `discord_gate_exempt=true` for users if the target environment enforces Discord gating.
4. Allocate enough quota, such as `500000000` internal quota units per test user.
5. Create or select a Fireworks channel with channel type `41`.
6. Attach Fireworks provider keys to the test channel without exposing them in logs.
7. Create NashiYard tokens for the test users and store them as YouziLoadLab secrets.
8. Verify `/v1/models` and a single `/v1/chat/completions` request before pressure traffic.

## Local Locust Command

Run from the repository root. Replace values with a safe target and token.

```powershell
py -3.13 -m locust `
  -f runner/youziloadlab_runner/scenarios/nashiyard_fireworks_channel.py `
  --headless `
  --host https://nashiyard.example.com `
  --users 5 `
  --spawn-rate 2 `
  --run-time 60s `
  --token sk-test-user-token `
  --model accounts/fireworks/models/llama-v3p1-8b-instruct `
  --prompt "Say hello in 50 words or less." `
  --max-tokens 128 `
  --temperature 0.7 `
  --stream-ratio 0.1
```

For a full pass, repeat the command with the phase table values. Save each run's CSV or API report output so the final report can compare phases.

## Expected Request Shape

The Locust user posts to `/v1/chat/completions` with an OpenAI-compatible payload built by `build_chat_payload()`:

```json
{
  "model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
  "messages": [
    {"role": "user", "content": "Say hello in 50 words or less."}
  ],
  "max_tokens": 128,
  "temperature": 0.7,
  "stream": false
}
```

Streaming is selected per request using `--stream-ratio`. A value of `0` disables streaming; a value of `1` makes every request streaming.

## What to Watch

Track these outcome classes in Locust output, YouziLoadLab reports, and NashiYard logs:

- `2xx` successful chat completions.
- `401`, `402`, and `403` auth, quota, or permission problems.
- `412` Fireworks/provider precondition or upstream-routing failures.
- `429` rate limits from NashiYard or Fireworks.
- `307` redirects that may indicate unexpected routing behavior.
- `5xx` gateway or provider errors.
- Timeouts and connection resets.
- Error bodies that accidentally include provider keys or bearer tokens.

## Success Criteria

- The smoke phase completes with no unexpected auth failures.
- The peak phase records p95/p99 latency and failure rate without crashing NashiYard.
- `412`, `429`, `5xx`, timeout, and auth failures are separated in analysis notes.
- No response body, report note, or log excerpt contains a plaintext Fireworks key or bearer token.
- Cleanup is performed manually or explicitly deferred with the reason recorded in the report.

## Cleanup Checklist

After the run:

1. Revoke or delete test tokens unless they are intentionally retained for a repeat run.
2. Disable or delete the test Fireworks channel if it was created only for this exercise.
3. Remove test users or leave them disabled with a clear owner label.
4. Confirm Fireworks keys are not stored in exported reports.
5. Archive run settings, metrics, and operator notes under a dated report directory.
