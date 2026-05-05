# YouziLoadLab Scenario Suites Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement first-class scenario suites for NashiYard Fireworks channel stress testing, polling-system stress testing, generic OpenAI-compatible chat load, and smoke checks.

**Architecture:** Scenario suites live in `runner/youziloadlab_runner/scenarios` and expose deterministic helpers for unit tests plus Locust user classes for execution. NashiYard admin setup/cleanup uses `NashiYardAdminClient`; request construction uses shared payload helpers; report assertions use shared metrics and error classification.

**Tech Stack:** Python 3.12, Locust, httpx, pytest, FastAPI run orchestration, SQLModel persisted runs/reports.

---

## Source Requirements

The Fireworks suite is based on `E:\cursor_project\nashiyard\nashiyard\docs\fireworks-stress-test-plan.md`:

- create isolated test users with prefix `stress_test_fw_`.
- use group `fireworks_stress`.
- set `discord_gate_exempt=true` for created users.
- allocate quota such as `500000000` internal quota units.
- create or reuse Fireworks channel type `41`.
- default model: `accounts/fireworks/models/llama-v3p1-8b-instruct`.
- support smoke phase and five full pressure phases.
- track 412, 429, 307, 5xx, 401/402/403, timeout, and sanitization failures.
- provide cleanup of test users/tokens/channel state.

The polling suite targets NashiYard operational behavior around periodic polling pressure:

- periodic channel list/status checks.
- optional channel test/check endpoints when available.
- repeated model/token/usage observation calls.
- mixed background polling plus foreground `/v1/chat/completions` traffic.
- measurable impact on latency, failures, and admin endpoint health.

---

## Scenario Config Files

Create these docs and schemas during implementation:

- `docs/scenario-authoring.md`: how to add a new scenario.
- `docs/scenarios/fireworks-channel.md`: operator guide for Fireworks stress testing.
- `docs/scenarios/polling-system.md`: operator guide for polling stress testing.
- `runner/youziloadlab_runner/scenarios/config_schemas.py`: JSON schemas used by API and WebUI.
- `runner/tests/test_scenario_schemas.py`: validates required fields and defaults.

---

### Task 1: Shared Scenario Config Schemas

**Files:**
- Create: `runner/youziloadlab_runner/scenarios/config_schemas.py`
- Create: `runner/tests/test_scenario_schemas.py`

- [ ] **Step 1: Write failing schema tests**

Create `runner/tests/test_scenario_schemas.py`:

```python
from youziloadlab_runner.scenarios.config_schemas import FIREWORKS_SCHEMA, POLLING_SCHEMA


def test_fireworks_schema_requires_setup_request_load_and_cleanup() -> None:
    assert FIREWORKS_SCHEMA["required"] == ["setup", "request", "loadProfile", "cleanup"]
    assert FIREWORKS_SCHEMA["properties"]["setup"]["properties"]["testUserPrefix"]["default"] == "stress_test_fw_"
    assert FIREWORKS_SCHEMA["properties"]["setup"]["properties"]["testUserGroup"]["default"] == "fireworks_stress"


def test_polling_schema_requires_polling_and_load_profile() -> None:
    assert POLLING_SCHEMA["required"] == ["polling", "loadProfile"]
    assert "channelListIntervalSeconds" in POLLING_SCHEMA["properties"]["polling"]["properties"]
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest runner/tests/test_scenario_schemas.py -q`
Expected: fail because `config_schemas.py` does not exist.

- [ ] **Step 3: Implement schemas**

Create `runner/youziloadlab_runner/scenarios/config_schemas.py`:

```python
FIREWORKS_SCHEMA: dict = {
    "type": "object",
    "required": ["setup", "request", "loadProfile", "cleanup"],
    "properties": {
        "setup": {
            "type": "object",
            "properties": {
                "createUsers": {"type": "boolean", "default": True},
                "testUserPrefix": {"type": "string", "default": "stress_test_fw_"},
                "testUserCount": {"type": "integer", "default": 3, "minimum": 1, "maximum": 100},
                "testUserGroup": {"type": "string", "default": "fireworks_stress"},
                "quotaPerUser": {"type": "integer", "default": 500000000, "minimum": 1},
                "discordGateExempt": {"type": "boolean", "default": True},
                "createChannel": {"type": "boolean", "default": True},
                "channelName": {"type": "string", "default": "fireworks_stress_main"},
                "channelType": {"type": "integer", "default": 41},
                "fireworksBaseUrl": {"type": "string", "default": "https://api.fireworks.ai/inference/v1"},
            },
        },
        "request": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "default": "accounts/fireworks/models/llama-v3p1-8b-instruct"},
                "prompt": {"type": "string", "default": "Say hello in 50 words or less."},
                "maxTokens": {"type": "integer", "default": 128, "minimum": 1, "maximum": 4096},
                "temperature": {"type": "number", "default": 0.7, "minimum": 0, "maximum": 2},
                "streamRatio": {"type": "number", "default": 0.1, "minimum": 0, "maximum": 1},
                "timeoutSeconds": {"type": "integer", "default": 30, "minimum": 1, "maximum": 300},
            },
        },
        "loadProfile": {"type": "object", "properties": {"phases": {"type": "array"}}},
        "cleanup": {
            "type": "object",
            "properties": {
                "deleteUsers": {"type": "boolean", "default": False},
                "deleteTokens": {"type": "boolean", "default": True},
                "disableCreatedChannel": {"type": "boolean", "default": True},
            },
        },
    },
}

POLLING_SCHEMA: dict = {
    "type": "object",
    "required": ["polling", "loadProfile"],
    "properties": {
        "polling": {
            "type": "object",
            "properties": {
                "channelListIntervalSeconds": {"type": "integer", "default": 5, "minimum": 1},
                "tokenListIntervalSeconds": {"type": "integer", "default": 10, "minimum": 1},
                "usageIntervalSeconds": {"type": "integer", "default": 15, "minimum": 1},
                "includeForegroundChat": {"type": "boolean", "default": True},
                "foregroundChatRatio": {"type": "number", "default": 0.3, "minimum": 0, "maximum": 1},
            },
        },
        "loadProfile": {"type": "object", "properties": {"phases": {"type": "array"}}},
    },
}
```

- [ ] **Step 4: Run tests and commit**

Run: `pytest runner/tests/test_scenario_schemas.py -q`
Expected: `2 passed`.

Run:

```powershell
git add runner/youziloadlab_runner/scenarios/config_schemas.py runner/tests/test_scenario_schemas.py
git commit -m "feat(runner): add scenario config schemas"
```

---

### Task 2: Fireworks Setup Planner

**Files:**
- Create: `runner/youziloadlab_runner/scenarios/nashiyard_fireworks_channel.py`
- Create: `runner/tests/test_fireworks_scenario.py`

- [ ] **Step 1: Write failing setup planner tests**

Create `runner/tests/test_fireworks_scenario.py`:

```python
from youziloadlab_runner.scenarios.nashiyard_fireworks_channel import build_test_usernames, default_fireworks_phases


def test_build_test_usernames_are_zero_padded_and_isolated() -> None:
    assert build_test_usernames("stress_test_fw_", 3) == [
        "stress_test_fw_001",
        "stress_test_fw_002",
        "stress_test_fw_003",
    ]


def test_default_fireworks_phases_match_design_document() -> None:
    phases = default_fireworks_phases()
    assert [phase.name for phase in phases] == ["smoke", "baseline", "ramp", "peak", "fault_injection", "recovery"]
    assert phases[0].duration_seconds == 60
    assert phases[0].users == 5
    assert phases[3].users == 100
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest runner/tests/test_fireworks_scenario.py -q`
Expected: fail because Fireworks scenario does not exist.

- [ ] **Step 3: Implement planner helpers**

Create `runner/youziloadlab_runner/scenarios/nashiyard_fireworks_channel.py`:

```python
from locust import HttpUser, between, task

from youziloadlab_runner.contracts import LoadPhase
from youziloadlab_runner.payloads import build_chat_payload
from youziloadlab_runner.scenarios.openai_chat_load import build_headers, should_stream


def build_test_usernames(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{index:03d}" for index in range(1, count + 1)]


def default_fireworks_phases() -> list[LoadPhase]:
    return [
        LoadPhase("smoke", 60, 5, 2),
        LoadPhase("baseline", 300, 10, 2),
        LoadPhase("ramp", 600, 50, 5),
        LoadPhase("peak", 300, 100, 10),
        LoadPhase("fault_injection", 600, 30, 3),
        LoadPhase("recovery", 300, 20, 2),
    ]


class NashiYardFireworksUser(HttpUser):
    wait_time = between(0.1, 1.0)

    @task
    def chat_completion(self) -> None:
        token = self.environment.parsed_options.token
        model = self.environment.parsed_options.model
        prompt = self.environment.parsed_options.prompt
        stream_ratio = float(self.environment.parsed_options.stream_ratio)
        stream = should_stream(stream_ratio)
        self.client.post(
            "/v1/chat/completions",
            headers=build_headers(token),
            json=build_chat_payload(
                model=model,
                prompt=prompt,
                max_tokens=int(self.environment.parsed_options.max_tokens),
                temperature=float(self.environment.parsed_options.temperature),
                stream=stream,
            ),
            name="Fireworks /v1/chat/completions",
        )
```

- [ ] **Step 4: Run tests and commit**

Run: `pytest runner/tests/test_fireworks_scenario.py -q`
Expected: `2 passed`.

Run:

```powershell
git add runner/youziloadlab_runner/scenarios/nashiyard_fireworks_channel.py runner/tests/test_fireworks_scenario.py
git commit -m "feat(runner): add fireworks scenario planner"
```

---

### Task 3: Polling Scenario Planner

**Files:**
- Create: `runner/youziloadlab_runner/scenarios/nashiyard_polling_system.py`
- Create: `runner/tests/test_polling_scenario.py`

- [ ] **Step 1: Write failing polling tests**

Create `runner/tests/test_polling_scenario.py`:

```python
from youziloadlab_runner.scenarios.nashiyard_polling_system import build_polling_tasks, should_run_foreground_chat


def test_build_polling_tasks_uses_intervals() -> None:
    tasks = build_polling_tasks(
        channel_list_interval_seconds=5,
        token_list_interval_seconds=10,
        usage_interval_seconds=15,
    )
    assert tasks == [
        {"name": "channel_list", "path": "/api/channel/", "interval_seconds": 5},
        {"name": "token_list", "path": "/api/token/", "interval_seconds": 10},
        {"name": "usage", "path": "/api/log/self", "interval_seconds": 15},
    ]


def test_should_run_foreground_chat_uses_ratio() -> None:
    assert should_run_foreground_chat(0.0, random_value=0.0) is False
    assert should_run_foreground_chat(1.0, random_value=0.99) is True
    assert should_run_foreground_chat(0.3, random_value=0.2) is True
    assert should_run_foreground_chat(0.3, random_value=0.4) is False
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest runner/tests/test_polling_scenario.py -q`
Expected: fail because polling scenario does not exist.

- [ ] **Step 3: Implement polling helpers and Locust user**

Create `runner/youziloadlab_runner/scenarios/nashiyard_polling_system.py`:

```python
import random

from locust import HttpUser, between, task

from youziloadlab_runner.payloads import build_chat_payload
from youziloadlab_runner.scenarios.openai_chat_load import build_headers


def build_polling_tasks(
    *, channel_list_interval_seconds: int, token_list_interval_seconds: int, usage_interval_seconds: int
) -> list[dict]:
    return [
        {"name": "channel_list", "path": "/api/channel/", "interval_seconds": channel_list_interval_seconds},
        {"name": "token_list", "path": "/api/token/", "interval_seconds": token_list_interval_seconds},
        {"name": "usage", "path": "/api/log/self", "interval_seconds": usage_interval_seconds},
    ]


def should_run_foreground_chat(ratio: float, *, random_value: float | None = None) -> bool:
    value = random.random() if random_value is None else random_value
    return value < ratio


class NashiYardPollingUser(HttpUser):
    wait_time = between(0.1, 1.0)

    @task(3)
    def poll_channel_list(self) -> None:
        self.client.get("/api/channel/", name="Polling GET /api/channel/")

    @task(2)
    def poll_token_list(self) -> None:
        self.client.get("/api/token/", name="Polling GET /api/token/")

    @task(1)
    def poll_usage(self) -> None:
        self.client.get("/api/log/self", name="Polling GET /api/log/self")

    @task(2)
    def foreground_chat(self) -> None:
        ratio = float(self.environment.parsed_options.foreground_chat_ratio)
        if not should_run_foreground_chat(ratio):
            return
        token = self.environment.parsed_options.token
        self.client.post(
            "/v1/chat/completions",
            headers=build_headers(token),
            json=build_chat_payload(
                model=self.environment.parsed_options.model,
                prompt="Short health check response.",
                max_tokens=64,
                temperature=0.2,
                stream=False,
            ),
            name="Polling foreground chat",
        )
```

- [ ] **Step 4: Run tests and commit**

Run: `pytest runner/tests/test_polling_scenario.py -q`
Expected: `2 passed`.

Run:

```powershell
git add runner/youziloadlab_runner/scenarios/nashiyard_polling_system.py runner/tests/test_polling_scenario.py
git commit -m "feat(runner): add polling scenario planner"
```

---

### Task 4: Smoke Check Scenario

**Files:**
- Create: `runner/youziloadlab_runner/scenarios/smoke_check.py`
- Create: `runner/tests/test_smoke_check.py`

- [ ] **Step 1: Write failing smoke check tests**

Create `runner/tests/test_smoke_check.py`:

```python
from youziloadlab_runner.scenarios.smoke_check import build_smoke_checks


def test_smoke_checks_cover_health_models_chat_and_sanitization() -> None:
    checks = build_smoke_checks()
    assert [check["name"] for check in checks] == ["health", "models", "chat", "invalid_key_sanitization"]
    assert checks[0]["method"] == "GET"
    assert checks[2]["path"] == "/v1/chat/completions"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest runner/tests/test_smoke_check.py -q`
Expected: fail because smoke scenario does not exist.

- [ ] **Step 3: Implement smoke check helpers**

Create `runner/youziloadlab_runner/scenarios/smoke_check.py`:

```python
def build_smoke_checks() -> list[dict]:
    return [
        {"name": "health", "method": "GET", "path": "/api/health"},
        {"name": "models", "method": "GET", "path": "/v1/models"},
        {"name": "chat", "method": "POST", "path": "/v1/chat/completions"},
        {"name": "invalid_key_sanitization", "method": "POST", "path": "/v1/chat/completions"},
    ]
```

- [ ] **Step 4: Run tests and commit**

Run: `pytest runner/tests/test_smoke_check.py -q`
Expected: `1 passed`.

Run:

```powershell
git add runner/youziloadlab_runner/scenarios/smoke_check.py runner/tests/test_smoke_check.py
git commit -m "feat(runner): add smoke check scenario"
```

---

### Task 5: Scenario Operator Documentation

**Files:**
- Create: `docs/scenario-authoring.md`
- Create: `docs/scenarios/fireworks-channel.md`
- Create: `docs/scenarios/polling-system.md`

- [ ] **Step 1: Create authoring guide**

Create `docs/scenario-authoring.md`:

```markdown
# Scenario Authoring

A scenario has three parts:

1. A JSON schema in `runner/youziloadlab_runner/scenarios/config_schemas.py`.
2. Unit-testable helper functions in `runner/youziloadlab_runner/scenarios/<scenario>.py`.
3. A Locust `HttpUser` class when the scenario generates pressure traffic.

Rules:

- Keep setup and cleanup logic outside WebUI code.
- Keep request payload construction in `payloads.py` unless it is scenario-specific.
- Add tests for helper functions before adding Locust classes.
- Redact secrets from event messages and report notes.
```

- [ ] **Step 2: Create Fireworks operator guide**

Create `docs/scenarios/fireworks-channel.md`:

```markdown
# NashiYard Fireworks Channel Stress Scenario

## Purpose

Validate Fireworks channel stability, retry behavior, multi-key behavior, 412 handling, error sanitization, and recovery behavior under controlled pressure.

## Defaults

- Test user prefix: `stress_test_fw_`
- Test group: `fireworks_stress`
- Channel type: `41`
- Model: `accounts/fireworks/models/llama-v3p1-8b-instruct`
- Quota per user: `500000000`
- Discord gate exempt: `true`

## Phases

| Phase | Duration | Users | Spawn Rate |
| --- | ---: | ---: | ---: |
| smoke | 60s | 5 | 2 |
| baseline | 300s | 10 | 2 |
| ramp | 600s | 50 | 5 |
| peak | 300s | 100 | 10 |
| fault_injection | 600s | 30 | 3 |
| recovery | 300s | 20 | 2 |

## Success Criteria

- Smoke phase has zero unexpected auth failures.
- Peak phase records p95 latency and failure rate without crashing NashiYard.
- 412 errors are classified as `fireworks_412`.
- Error responses do not include provider keys.
- Cleanup plan is executed or explicitly skipped by the operator.
```

- [ ] **Step 3: Create polling operator guide**

Create `docs/scenarios/polling-system.md`:

```markdown
# NashiYard Polling System Stress Scenario

## Purpose

Measure the impact of repeated polling-style admin and user observation requests on NashiYard while foreground chat traffic continues.

## Default Polling Tasks

| Name | Path | Default Interval |
| --- | --- | ---: |
| channel_list | `/api/channel/` | 5s |
| token_list | `/api/token/` | 10s |
| usage | `/api/log/self` | 15s |

## Mixed Traffic

The scenario can mix polling requests with `/v1/chat/completions` traffic. The default foreground chat ratio is `0.3`.

## Success Criteria

- Polling endpoints remain responsive.
- Foreground chat p95 latency does not degrade beyond the operator-defined threshold.
- Admin endpoints do not leak secrets or panic under repeated access.
- The report separates polling failures from foreground chat failures.
```

- [ ] **Step 4: Commit docs**

Run:

```powershell
git add docs/scenario-authoring.md docs/scenarios/fireworks-channel.md docs/scenarios/polling-system.md
git commit -m "docs: add scenario operator guides"
```

---

## Self-Review

### Spec coverage

- Fireworks plan: covered by schema defaults, setup planner, phases, docs, and error classifications from implementation plan.
- Polling system: covered by polling schema, polling tasks, mixed foreground traffic, and operator documentation.
- Generic OpenAI pressure: covered by implementation plan Task 10 and reused in Fireworks/Polling.
- Smoke checks: covered by Task 4.
- Future scenario extensibility: covered by scenario authoring guide.

### Placeholder scan

This plan contains no vague “add tests later” instructions. Every task includes file paths, code, commands, and expected results.

### Type consistency

Scenario IDs match the architecture and implementation plan: `openai-chat-load`, `nashiyard-fireworks-channel`, `nashiyard-polling-system`, and `smoke-check`.
