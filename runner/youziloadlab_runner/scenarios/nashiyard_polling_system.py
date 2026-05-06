import os
import random
import sys
from typing import Any, TypedDict

if "pytest" in sys.modules:
    os.environ.setdefault("LOCUST_SKIP_MONKEY_PATCH", "1")

from locust import HttpUser, between, events, task

from youziloadlab_runner.payloads import build_chat_payload
from youziloadlab_runner.scenarios.openai_chat_load import build_headers


class PollingTask(TypedDict):
    name: str
    path: str
    interval_seconds: int


def build_polling_tasks(
    *,
    channel_list_interval_seconds: int,
    token_list_interval_seconds: int,
    usage_interval_seconds: int,
) -> list[PollingTask]:
    return [
        {
            "name": "channel_list",
            "path": "/api/channel/",
            "interval_seconds": channel_list_interval_seconds,
        },
        {
            "name": "token_list",
            "path": "/api/token/",
            "interval_seconds": token_list_interval_seconds,
        },
        {
            "name": "usage",
            "path": "/api/log/self",
            "interval_seconds": usage_interval_seconds,
        },
    ]


def should_run_foreground_chat(ratio: float, *, random_value: float | None = None) -> bool:
    clamped_ratio = min(max(ratio, 0.0), 1.0)
    value = random.random() if random_value is None else random_value
    return value < clamped_ratio


def build_polling_headers(*, auth_header: str = "", cookie: str = "") -> dict[str, str]:
    headers: dict[str, str] = {}
    if auth_header:
        headers["Authorization"] = auth_header
    if cookie:
        headers["Cookie"] = cookie
    return headers


def _get_option(parsed_options: Any, name: str, default: Any) -> Any:
    return getattr(parsed_options, name, default)


@events.init_command_line_parser.add_listener  # type: ignore[untyped-decorator]
def add_polling_options(parser: Any) -> None:
    parser.add_argument(
        "--foreground-chat-ratio",
        env_var="YOUZILOADLAB_FOREGROUND_CHAT_RATIO",
        type=float,
        default=0.3,
    )
    parser.add_argument(
        "--polling-auth-header",
        env_var="YOUZILOADLAB_POLLING_AUTH_HEADER",
        default="",
    )
    parser.add_argument(
        "--polling-cookie",
        env_var="YOUZILOADLAB_POLLING_COOKIE",
        default="",
    )
    parser.add_argument(
        "--polling-prompt",
        env_var="YOUZILOADLAB_POLLING_PROMPT",
        default="Short health check response.",
    )
    parser.add_argument(
        "--polling-max-tokens",
        env_var="YOUZILOADLAB_POLLING_MAX_TOKENS",
        type=int,
        default=64,
    )
    parser.add_argument(
        "--polling-temperature",
        env_var="YOUZILOADLAB_POLLING_TEMPERATURE",
        type=float,
        default=0.2,
    )


class NashiYardPollingUser(HttpUser):
    wait_time = between(0.1, 1.0)

    @task(3)
    def poll_channel_list(self) -> None:
        self.client.get(
            "/api/channel/",
            headers=self._polling_headers(),
            name="Polling GET /api/channel/",
        )

    @task(2)
    def poll_token_list(self) -> None:
        self.client.get(
            "/api/token/",
            headers=self._polling_headers(),
            name="Polling GET /api/token/",
        )

    @task(1)
    def poll_usage(self) -> None:
        self.client.get(
            "/api/log/self",
            headers=self._polling_headers(),
            name="Polling GET /api/log/self",
        )

    @task(2)
    def foreground_chat(self) -> None:
        parsed_options = self.environment.parsed_options
        foreground_chat_ratio = float(_get_option(parsed_options, "foreground_chat_ratio", 0.3))
        if not should_run_foreground_chat(foreground_chat_ratio):
            return

        token = str(_get_option(parsed_options, "token", ""))
        model = str(_get_option(parsed_options, "model", "gpt-4o-mini"))
        prompt = str(_get_option(parsed_options, "polling_prompt", "Short health check response."))
        max_tokens = int(_get_option(parsed_options, "polling_max_tokens", 64))
        temperature = float(_get_option(parsed_options, "polling_temperature", 0.2))

        self.client.post(
            "/v1/chat/completions",
            headers=build_headers(token),
            json=build_chat_payload(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
            ),
            name="Polling foreground chat",
        )

    def _polling_headers(self) -> dict[str, str]:
        parsed_options = self.environment.parsed_options
        return build_polling_headers(
            auth_header=str(_get_option(parsed_options, "polling_auth_header", "")),
            cookie=str(_get_option(parsed_options, "polling_cookie", "")),
        )
