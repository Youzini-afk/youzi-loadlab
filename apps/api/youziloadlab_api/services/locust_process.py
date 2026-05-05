from dataclasses import dataclass, field


@dataclass(frozen=True)
class LocustLaunchResult:
    web_url: str
    pid: int | None
    command: list[str] = field(default_factory=list)
    started: bool = False


class LocustProcessManager:
    def __init__(self, web_path_prefix: str = "/locust") -> None:
        self.web_path_prefix = web_path_prefix.rstrip("/")

    def launch_placeholder(self, run_id: str) -> LocustLaunchResult:
        return LocustLaunchResult(
            web_url=f"{self.web_path_prefix}/{run_id}",
            pid=None,
            command=[],
            started=False,
        )
