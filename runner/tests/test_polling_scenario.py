from youziloadlab_runner.scenarios.nashiyard_polling_system import (
    build_polling_tasks,
    should_run_foreground_chat,
)


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


def test_should_run_foreground_chat_clamps_ratio() -> None:
    assert should_run_foreground_chat(-1.0, random_value=0.0) is False
    assert should_run_foreground_chat(2.0, random_value=0.99) is True
