import os
import random
import sys
from typing import Any

if "pytest" in sys.modules:
    os.environ.setdefault("LOCUST_SKIP_MONKEY_PATCH", "1")

from locust import HttpUser, between, events, task

from youziloadlab_runner.payloads import build_chat_payload


def build_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def should_stream(stream_ratio: float, *, random_value: float | None = None) -> bool:
    ratio = min(max(stream_ratio, 0.0), 1.0)
    value = random.random() if random_value is None else random_value
    return value < ratio


def _get_option(parsed_options: Any, name: str, default: Any) -> Any:
    return getattr(parsed_options, name, default)


@events.init_command_line_parser.add_listener  # type: ignore[untyped-decorator]
def add_openai_chat_options(parser: Any) -> None:
    parser.add_argument("--token", env_var="YOUZILOADLAB_TOKEN", default="")
    parser.add_argument("--model", env_var="YOUZILOADLAB_MODEL", default="gpt-4o-mini")
    parser.add_argument("--prompt", env_var="YOUZILOADLAB_PROMPT", default="Say hello in one sentence.")
    parser.add_argument("--max-tokens", env_var="YOUZILOADLAB_MAX_TOKENS", type=int, default=128)
    parser.add_argument("--temperature", env_var="YOUZILOADLAB_TEMPERATURE", type=float, default=0.2)
    parser.add_argument("--stream-ratio", env_var="YOUZILOADLAB_STREAM_RATIO", type=float, default=0.0)


class OpenAIChatUser(HttpUser):
    wait_time = between(0.1, 1.0)

    @task
    def chat_completion(self) -> None:
        parsed_options = self.environment.parsed_options
        token = str(_get_option(parsed_options, "token", ""))
        model = str(_get_option(parsed_options, "model", "gpt-4o-mini"))
        prompt = str(_get_option(parsed_options, "prompt", "Say hello in one sentence."))
        max_tokens = int(_get_option(parsed_options, "max_tokens", 128))
        temperature = float(_get_option(parsed_options, "temperature", 0.2))
        stream_ratio = float(_get_option(parsed_options, "stream_ratio", 0.0))

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
            name="POST /v1/chat/completions",
        )
