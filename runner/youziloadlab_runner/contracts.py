from dataclasses import dataclass, field


@dataclass(frozen=True)
class LoadPhase:
    name: str
    duration_seconds: int
    users: int
    spawn_rate: float


@dataclass(frozen=True)
class RequestResult:
    request_id: str
    status_code: int
    latency_ms: float
    success: bool
    error_type: str | None = None
    error_detail: str | None = None
    tokens_used: int = 0
    tags: dict[str, str] = field(default_factory=dict)

