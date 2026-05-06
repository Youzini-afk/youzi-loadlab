import json
import os
import sys
from typing import Any

if "pytest" in sys.modules:
    os.environ.setdefault("LOCUST_SKIP_MONKEY_PATCH", "1")

from locust import HttpUser, LoadTestShape, between, task

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


def fireworks_phases_json(phases: list[LoadPhase]) -> str:
    return json.dumps(
        [
            {
                "name": phase.name,
                "durationSeconds": phase.duration_seconds,
                "users": phase.users,
                "spawnRate": phase.spawn_rate,
            }
            for phase in phases
        ],
        separators=(",", ":"),
    )


def load_fireworks_phases_from_env(value: str | None = None) -> list[LoadPhase]:
    raw_value = os.environ.get("YOUZILOADLAB_PHASES_JSON") if value is None else value
    if not raw_value:
        return []
    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    phases: list[LoadPhase] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        phases.append(
            LoadPhase(
                name=str(item.get("name", f"phase_{len(phases) + 1}")),
                duration_seconds=_positive_int(
                    item.get("durationSeconds", item.get("duration_seconds")),
                    default=60,
                ),
                users=_positive_int(item.get("users"), default=1),
                spawn_rate=_positive_float(
                    item.get("spawnRate", item.get("spawn_rate")),
                    default=1,
                ),
            )
        )
    return phases


def _get_option(parsed_options: Any, name: str, default: Any) -> Any:
    return getattr(parsed_options, name, default)


class NashiYardFireworksUser(HttpUser):
    wait_time = between(0.1, 1.0)

    @task
    def chat_completion(self) -> None:
        parsed_options = self.environment.parsed_options
        token = str(_get_option(parsed_options, "token", ""))
        model = str(
            _get_option(parsed_options, "model", "accounts/fireworks/models/llama-v3p1-8b-instruct")
        )
        prompt = str(_get_option(parsed_options, "prompt", "Say hello in 50 words or less."))
        max_tokens = int(_get_option(parsed_options, "max_tokens", 128))
        temperature = float(_get_option(parsed_options, "temperature", 0.7))
        stream_ratio = float(_get_option(parsed_options, "stream_ratio", 0.1))

        self.client.post(
            "/v1/chat/completions",
            headers=build_headers(token),
            json=build_chat_payload(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=should_stream(stream_ratio),
            ),
            name="Fireworks /v1/chat/completions",
        )


_ENV_FIREWORKS_PHASES = load_fireworks_phases_from_env()

if _ENV_FIREWORKS_PHASES:

    class FireworksPhaseShape(LoadTestShape):
        phases = _ENV_FIREWORKS_PHASES

        def tick(self) -> tuple[int, float] | None:
            elapsed = self.get_run_time()  # type: ignore[no-untyped-call]
            total = 0
            for phase in self.phases:
                total += phase.duration_seconds
                if elapsed < total:
                    return phase.users, phase.spawn_rate
            return None


def _positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _positive_float(value: Any, *, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
