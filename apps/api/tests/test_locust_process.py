from pathlib import Path

from youziloadlab_api.services.locust_process import (
    build_locust_env,
    load_execution_profile,
    parse_locust_stats_csv,
)


def test_load_execution_profile_prefers_first_phase() -> None:
    profile = load_execution_profile(
        {
            "loadProfile": {
                "users": 99,
                "phases": [
                    {"users": 5, "spawnRate": 2, "durationSeconds": 60},
                    {"users": 50, "spawnRate": 5, "durationSeconds": 600},
                ],
            }
        }
    )

    assert profile.users == 5
    assert profile.spawn_rate == 2
    assert profile.duration_seconds == 60


def test_build_locust_env_uses_request_values_without_command_line_secrets() -> None:
    env = build_locust_env(
        {
            "request": {
                "token": "sk-test-secret",
                "model": "gpt-4o-mini",
                "prompt": "hello",
                "maxTokens": 64,
                "temperature": 0.3,
                "streamRatio": 0.2,
            }
        }
    )

    assert env["YOUZILOADLAB_TOKEN"] == "sk-test-secret"
    assert env["YOUZILOADLAB_MODEL"] == "gpt-4o-mini"
    assert env["YOUZILOADLAB_MAX_TOKENS"] == "64"
    assert env["YOUZILOADLAB_STREAM_RATIO"] == "0.2"


def test_parse_locust_stats_csv_reads_aggregated_row(tmp_path: Path) -> None:
    stats_path = tmp_path / "locust_stats.csv"
    stats_path.write_text(
        "\n".join(
            [
                "Type,Name,Request Count,Failure Count,Average Response Time,Requests/s,50%,90%,95%,99%",
                "POST,/v1/chat/completions,3,1,100,1.5,90,140,150,200",
                ",Aggregated,10,2,120,2.5,100,160,180,240",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = parse_locust_stats_csv(stats_path)

    assert snapshot is not None
    assert snapshot.requests_total == 10
    assert snapshot.failures_total == 2
    assert snapshot.avg_latency_ms == 120
    assert snapshot.p95_latency_ms == 180
    assert snapshot.p99_latency_ms == 240
