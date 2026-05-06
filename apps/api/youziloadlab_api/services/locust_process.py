import csv
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from youziloadlab_api.core.security import redact_sensitive_text


SCENARIO_LOCUSTFILES = {
    "openai-chat-load": "runner/youziloadlab_runner/scenarios/openai_chat_load.py",
    "nashiyard-fireworks-channel": "runner/youziloadlab_runner/scenarios/nashiyard_fireworks_channel.py",
    "nashiyard-polling-system": "runner/youziloadlab_runner/scenarios/nashiyard_polling_system.py",
    "smoke-check": "runner/youziloadlab_runner/scenarios/openai_chat_load.py",
}


@dataclass(frozen=True)
class LoadExecutionProfile:
    users: int = 1
    spawn_rate: float = 1
    duration_seconds: int = 30


@dataclass(frozen=True)
class LocustLaunchResult:
    web_url: str
    pid: int | None
    command: list[str] = field(default_factory=list)
    started: bool = False
    workdir: str | None = None
    artifacts: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LocustMetricSnapshot:
    requests_total: int
    failures_total: int
    current_rps: float
    avg_latency_ms: float
    p50_latency_ms: float
    p90_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float


class LocustProcessManager:
    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        runner_workdir: Path | str,
        web_path_prefix: str = "/locust",
    ) -> None:
        self.repo_root = repo_root or Path(__file__).resolve().parents[4]
        self.runner_workdir = Path(runner_workdir)
        self.web_path_prefix = web_path_prefix.rstrip("/")
        self._processes: dict[int, subprocess.Popen[bytes]] = {}

    def prepare_workdir(self, run_id: str) -> Path:
        workdir = self.runner_workdir / run_id
        workdir.mkdir(parents=True, exist_ok=True)
        return workdir

    def write_manifest(
        self,
        *,
        run_id: str,
        scenario_id: str,
        target_base_url: str,
        config: dict[str, Any],
    ) -> Path:
        workdir = self.prepare_workdir(run_id)
        manifest_path = workdir / "runner-config.json"
        safe_config = json.loads(redact_sensitive_text(json.dumps(config, ensure_ascii=False)))
        manifest_path.write_text(
            json.dumps(
                {
                    "runId": run_id,
                    "scenarioId": scenario_id,
                    "targetBaseUrl": target_base_url,
                    "config": safe_config,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return manifest_path

    def build_command(
        self,
        *,
        scenario_id: str,
        target_base_url: str,
        config: dict[str, Any],
        workdir: Path,
    ) -> tuple[list[str], dict[str, str], dict[str, str]]:
        locustfile = self.repo_root / SCENARIO_LOCUSTFILES[scenario_id]
        profile = load_execution_profile(config)
        csv_prefix = workdir / "locust"
        html_report = workdir / "locust-report.html"
        artifacts = {
            "manifest": str(workdir / "runner-config.json"),
            "stdout": str(workdir / "runner.stdout.log"),
            "stderr": str(workdir / "runner.stderr.log"),
            "stats_csv": str(workdir / "locust_stats.csv"),
            "failures_csv": str(workdir / "locust_failures.csv"),
            "exceptions_csv": str(workdir / "locust_exceptions.csv"),
            "html": str(html_report),
        }
        command = [
            sys.executable,
            "-m",
            "locust",
            "-f",
            str(locustfile),
            "--headless",
            "--host",
            target_base_url.rstrip("/"),
            "--users",
            str(profile.users),
            "--spawn-rate",
            str(profile.spawn_rate),
            "--run-time",
            f"{profile.duration_seconds}s",
            "--csv",
            str(csv_prefix),
            "--html",
            str(html_report),
        ]
        return command, build_locust_env(config), artifacts

    def launch(
        self,
        *,
        run_id: str,
        scenario_id: str,
        target_base_url: str,
        config: dict[str, Any],
    ) -> LocustLaunchResult:
        workdir = self.prepare_workdir(run_id)
        self.write_manifest(
            run_id=run_id,
            scenario_id=scenario_id,
            target_base_url=target_base_url,
            config=config,
        )
        command, env_overrides, artifacts = self.build_command(
            scenario_id=scenario_id,
            target_base_url=target_base_url,
            config=config,
            workdir=workdir,
        )
        stdout_path = Path(artifacts["stdout"])
        stderr_path = Path(artifacts["stderr"])
        env = os.environ.copy()
        env.update(env_overrides)
        stdout = stdout_path.open("ab")
        stderr = stderr_path.open("ab")
        try:
            process = subprocess.Popen(
                command,
                cwd=self.repo_root,
                env=env,
                stdout=stdout,
                stderr=stderr,
            )
        finally:
            stdout.close()
            stderr.close()
        self._processes[process.pid] = process
        return LocustLaunchResult(
            web_url=f"{self.web_path_prefix}/{run_id}",
            pid=process.pid,
            command=redact_command(command),
            started=True,
            workdir=str(workdir),
            artifacts=artifacts,
        )

    def get_exit_code(self, pid: int | None) -> int | None:
        if pid is None:
            return None
        process = self._processes.get(pid)
        if process is None:
            return None
        return process.poll()

    def stop(self, pid: int | None) -> bool:
        if pid is None:
            return False
        process = self._processes.get(pid)
        if process is None:
            return False
        if process.poll() is not None:
            return True
        try:
            process.terminate()
        except ProcessLookupError:
            return True
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        return True

    def parse_latest_metrics(self, artifacts: dict[str, Any]) -> LocustMetricSnapshot | None:
        stats_path_value = artifacts.get("stats_csv")
        if not isinstance(stats_path_value, str):
            return None
        return parse_locust_stats_csv(Path(stats_path_value))


def load_execution_profile(config: dict[str, Any]) -> LoadExecutionProfile:
    load_profile = _dict_value(config, "loadProfile")
    phases = load_profile.get("phases")
    if isinstance(phases, list) and phases:
        phase_dicts = [phase for phase in phases if isinstance(phase, dict)]
        if phase_dicts:
            return LoadExecutionProfile(
                users=max(_positive_int(phase.get("users"), default=1) for phase in phase_dicts),
                spawn_rate=max(
                    _positive_float(
                        phase.get("spawnRate", phase.get("spawn_rate")),
                        default=1,
                    )
                    for phase in phase_dicts
                ),
                duration_seconds=sum(
                    _positive_int(
                        phase.get("durationSeconds", phase.get("duration_seconds")),
                        default=30,
                    )
                    for phase in phase_dicts
                ),
            )
    return LoadExecutionProfile(
        users=_positive_int(load_profile.get("users"), default=1),
        spawn_rate=_positive_float(
            load_profile.get("spawnRate", load_profile.get("spawn_rate")),
            default=1,
        ),
        duration_seconds=_positive_int(
            load_profile.get("durationSeconds", load_profile.get("duration_seconds")),
            default=30,
        ),
    )


def build_locust_env(config: dict[str, Any]) -> dict[str, str]:
    request = _dict_value(config, "request")
    polling = _dict_value(config, "polling")
    env = {
        "YOUZILOADLAB_TOKEN": str(request.get("token", "")),
        "YOUZILOADLAB_MODEL": str(request.get("model", "gpt-4o-mini")),
        "YOUZILOADLAB_PROMPT": str(request.get("prompt", "Say hello in one sentence.")),
        "YOUZILOADLAB_MAX_TOKENS": str(request.get("maxTokens", request.get("max_tokens", 128))),
        "YOUZILOADLAB_TEMPERATURE": str(request.get("temperature", 0.2)),
        "YOUZILOADLAB_STREAM_RATIO": str(request.get("streamRatio", request.get("stream_ratio", 0))),
    }
    if polling:
        env["YOUZILOADLAB_FOREGROUND_CHAT_RATIO"] = str(
            polling.get("foregroundChatRatio", polling.get("foreground_chat_ratio", 0.3))
        )
        env["YOUZILOADLAB_POLLING_AUTH_HEADER"] = str(polling.get("authHeader", ""))
        env["YOUZILOADLAB_POLLING_COOKIE"] = str(polling.get("cookie", ""))
        env["YOUZILOADLAB_POLLING_PROMPT"] = str(
            request.get("prompt", polling.get("prompt", "Short health check response."))
        )
        env["YOUZILOADLAB_POLLING_MAX_TOKENS"] = str(
            request.get("maxTokens", polling.get("maxTokens", 64))
        )
        env["YOUZILOADLAB_POLLING_TEMPERATURE"] = str(
            request.get("temperature", polling.get("temperature", 0.2))
        )
    load_profile = _dict_value(config, "loadProfile")
    phases = load_profile.get("phases")
    if isinstance(phases, list) and phases:
        env["YOUZILOADLAB_PHASES_JSON"] = json.dumps(phases, separators=(",", ":"))
    return env


def redact_command(command: list[str]) -> list[str]:
    return [redact_sensitive_text(part) for part in command]


def parse_locust_stats_csv(path: Path) -> LocustMetricSnapshot | None:
    if not path.is_file():
        return None
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows.extend(csv.DictReader(csv_file))
    if not rows:
        return None
    selected = next((row for row in rows if row.get("Name") == "Aggregated"), rows[-1])
    return LocustMetricSnapshot(
        requests_total=_positive_int(selected.get("Request Count"), default=0),
        failures_total=_positive_int(selected.get("Failure Count"), default=0),
        current_rps=_positive_float(selected.get("Requests/s"), default=0),
        avg_latency_ms=_positive_float(selected.get("Average Response Time"), default=0),
        p50_latency_ms=_positive_float(selected.get("50%"), default=0),
        p90_latency_ms=_positive_float(selected.get("90%"), default=0),
        p95_latency_ms=_positive_float(selected.get("95%"), default=0),
        p99_latency_ms=_positive_float(selected.get("99%"), default=0),
    )


def _dict_value(value: dict[str, Any], key: str) -> dict[str, Any]:
    item = value.get(key)
    return item if isinstance(item, dict) else {}


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
