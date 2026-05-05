import os
import sys
from typing import Any

if "pytest" in sys.modules:
    os.environ.setdefault("LOCUST_SKIP_MONKEY_PATCH", "1")

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
