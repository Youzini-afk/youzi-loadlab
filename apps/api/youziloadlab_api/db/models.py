from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel

from youziloadlab_api.core.time import utc_now


def new_id() -> str:
    return str(uuid4())


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)


class Target(TimestampMixin, table=True):
    __tablename__ = "targets"
    id: str = Field(default_factory=new_id, primary_key=True)
    name: str = Field(index=True, unique=True, min_length=1, max_length=120)
    kind: str = Field(index=True, min_length=1, max_length=40)
    base_url: str = Field(min_length=1, max_length=500)
    admin_username: str | None = Field(default=None, max_length=120)
    default_model: str | None = Field(default=None, max_length=200)


class Secret(TimestampMixin, table=True):
    __tablename__ = "secrets"
    id: str = Field(default_factory=new_id, primary_key=True)
    target_id: str | None = Field(default=None, foreign_key="targets.id", index=True)
    name: str = Field(index=True, min_length=1, max_length=120)
    kind: str = Field(index=True, min_length=1, max_length=40)
    ciphertext: str = Field(min_length=1)
    fingerprint: str = Field(index=True, min_length=10, max_length=10)


class ScenarioDefinition(TimestampMixin, table=True):
    __tablename__ = "scenario_definitions"
    id: str = Field(primary_key=True)
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="")
    version: str = Field(default="0.1.0", max_length=40)
    schema_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    enabled: bool = Field(default=True, index=True)


class Run(TimestampMixin, table=True):
    __tablename__ = "runs"
    id: str = Field(default_factory=new_id, primary_key=True)
    name: str = Field(min_length=1, max_length=160)
    target_id: str = Field(foreign_key="targets.id", index=True)
    scenario_id: str = Field(foreign_key="scenario_definitions.id", index=True)
    status: str = Field(default="created", index=True, max_length=40)
    config_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    locust_web_url: str | None = Field(default=None, max_length=500)
    started_at: datetime | None = Field(default=None)
    finished_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)


class RunEvent(SQLModel, table=True):
    __tablename__ = "run_events"
    id: int | None = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="runs.id", index=True)
    level: str = Field(default="info", max_length=20)
    event_type: str = Field(index=True, max_length=80)
    message: str
    payload_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)


class RunMetricsSnapshot(SQLModel, table=True):
    __tablename__ = "run_metrics_snapshots"
    id: int | None = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="runs.id", index=True)
    timestamp: datetime = Field(default_factory=utc_now, nullable=False, index=True)
    requests_total: int = 0
    failures_total: int = 0
    current_rps: float = 0
    avg_latency_ms: float = 0
    p50_latency_ms: float = 0
    p90_latency_ms: float = 0
    p95_latency_ms: float = 0
    p99_latency_ms: float = 0
    status_counts_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    error_counts_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    tokens_total: int = 0


class Report(TimestampMixin, table=True):
    __tablename__ = "reports"
    id: str = Field(default_factory=new_id, primary_key=True)
    run_id: str = Field(foreign_key="runs.id", unique=True, index=True)
    summary_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    markdown: str
