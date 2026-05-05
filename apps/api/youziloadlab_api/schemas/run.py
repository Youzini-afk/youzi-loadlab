from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RunCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    target_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    config_json: dict[str, Any] = Field(default_factory=dict)


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    target_id: str
    scenario_id: str
    status: str
    config_json: dict[str, Any]
    locust_web_url: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class RunEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str
    level: str
    event_type: str
    message: str
    created_at: datetime


class RunMetricsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str
    timestamp: datetime
    requests_total: int
    failures_total: int
    current_rps: float
    avg_latency_ms: float
    p50_latency_ms: float
    p90_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    tokens_total: int
