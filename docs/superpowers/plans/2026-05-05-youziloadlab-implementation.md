# YouziLoadLab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the YouziLoadLab V1 platform as a polished Zeabur-deployable WebUI application for NashiYard/OpenAI-compatible stress testing.

**Architecture:** Build a FastAPI product API, React WebUI, SQLModel persistence layer, encrypted secret store, and Locust-based runner package. Keep scenario execution in `runner/` and product workflows in `apps/api/` so future test classes can be added without rewriting the platform.

**Tech Stack:** Python 3.12, FastAPI, SQLModel, pytest, Locust, httpx, cryptography, React 18, Vite, MUI, Vitest, Docker, Zeabur.

---

## Implementation Rules

- Work in `E:\cursor_project\nashiyard\youziloadlab`.
- Initialize git with `git init` before Task 1 if `.git` does not exist.
- Write the test first, run it, implement the smallest passing code, rerun tests, then commit.
- Do not store or log plaintext secrets.
- Keep FastAPI orchestration in `apps/api`; keep pressure execution in `runner`.

---

### Task 1: Repository Skeleton and Tooling

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `pyproject.toml`
- Create: `package.json`
- Create: `pnpm-workspace.yaml`

- [ ] **Step 1: Create root README**

Create `README.md`:

```markdown
# YouziLoadLab

YouziLoadLab is an independently deployable WebUI load-testing platform for NashiYard and OpenAI-compatible API gateways.

## Goals

- Provide a polished WebUI for configuring targets, secrets, scenarios, runs, and reports.
- Use Locust as the execution engine instead of rebuilding concurrency and latency statistics from scratch.
- Support NashiYard Fireworks channel pressure testing in V1.
- Support polling-system pressure tests as a first-class scenario family.
- Deploy as a single Zeabur service with persistent storage mounted at `/data`.

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
pnpm install
pytest apps/api/tests runner/tests -q
uvicorn youziloadlab_api.main:app --app-dir apps/api --reload
```
```

- [ ] **Step 2: Create agent instructions**

Create `AGENTS.md`:

```markdown
# AGENTS.md - YouziLoadLab

## Project Mission

Build a polished Zeabur-deployable load-testing WebUI for NashiYard and OpenAI-compatible APIs.

## Architecture Rules

- Product API code lives in `apps/api/youziloadlab_api`.
- Load execution and scenario logic lives in `runner/youziloadlab_runner`.
- Web UI code lives in `apps/web/src`.
- Do not put NashiYard-specific setup logic in the WebUI.
- Do not put Locust user classes inside FastAPI modules.
- Do not log plaintext secrets.

## Testing

Run Python tests:

```powershell
pytest apps/api/tests runner/tests -q
```

Run Web tests:

```powershell
pnpm --filter @youziloadlab/web test
```
```

- [ ] **Step 3: Create ignore and env files**

Create `.gitignore`:

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
node_modules/
apps/web/dist/
.env
*.db
*.sqlite
/data/
runs/
artifacts/
.DS_Store
Thumbs.db
.vscode/
.idea/
```

Create `.env.example`:

```dotenv
APP_ENV=development
APP_NAME=YouziLoadLab
APP_SECRET_KEY=replace-with-32-plus-character-dev-secret
ADMIN_PASSWORD=replace-with-local-admin-password
DATABASE_URL=sqlite:///./youziloadlab.dev.db
DATA_DIR=./data
RUNNER_WORKDIR=./data/runs
MAX_CONCURRENT_RUNS=1
MAX_USERS_PER_RUN=200
ALLOW_PUBLIC_RUNS=false
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```

- [ ] **Step 4: Create Python project config**

Create `pyproject.toml`:

```toml
[project]
name = "youziloadlab"
version = "0.1.0"
description = "WebUI load-testing platform for NashiYard and OpenAI-compatible APIs"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "sqlmodel>=0.0.22",
  "httpx>=0.27.0",
  "pydantic-settings>=2.4.0",
  "cryptography>=43.0.0",
  "locust>=2.32.0",
  "python-multipart>=0.0.9",
  "orjson>=3.10.0"
]

[project.optional-dependencies]
dev = ["pytest>=8.3.0", "pytest-asyncio>=0.24.0", "ruff>=0.6.0", "mypy>=1.11.0"]

[tool.pytest.ini_options]
testpaths = ["apps/api/tests", "runner/tests"]
pythonpath = ["apps/api", "runner"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
mypy_path = ["apps/api", "runner"]
```

- [ ] **Step 5: Create frontend workspace config**

Create `package.json`:

```json
{
  "name": "youziloadlab-root",
  "private": true,
  "scripts": {
    "web:dev": "pnpm --filter @youziloadlab/web dev",
    "web:build": "pnpm --filter @youziloadlab/web build",
    "web:test": "pnpm --filter @youziloadlab/web test",
    "web:typecheck": "pnpm --filter @youziloadlab/web typecheck"
  },
  "packageManager": "pnpm@9.12.0"
}
```

Create `pnpm-workspace.yaml`:

```yaml
packages:
  - apps/web
```

- [ ] **Step 6: Run tooling smoke checks**

Run: `python -m pip install -e .[dev]`
Expected: dependencies install and package is editable.

- [ ] **Step 7: Commit**

Run:

```powershell
git add README.md AGENTS.md .gitignore .env.example pyproject.toml package.json pnpm-workspace.yaml
git commit -m "chore: initialize youziloadlab workspace"
```

---

### Task 2: FastAPI Settings and Health Endpoint

**Files:**
- Create: `apps/api/youziloadlab_api/__init__.py`
- Create: `apps/api/youziloadlab_api/main.py`
- Create: `apps/api/youziloadlab_api/core/config.py`
- Create: `apps/api/youziloadlab_api/core/time.py`
- Create: `apps/api/youziloadlab_api/modules/health/router.py`
- Create: `apps/api/tests/test_health.py`

- [ ] **Step 1: Write failing health test**

Create `apps/api/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_health_returns_app_status() -> None:
    client = TestClient(create_app())
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "YouziLoadLab"
    assert body["environment"] in {"development", "test"}
    assert "timestamp" in body
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/api/tests/test_health.py -q`
Expected: fail because `youziloadlab_api` does not exist yet.

- [ ] **Step 3: Implement settings and time helpers**

Create empty `apps/api/youziloadlab_api/__init__.py`.

Create `apps/api/youziloadlab_api/core/config.py`:

```python
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "YouziLoadLab"
    app_env: str = Field(default="development", alias="APP_ENV")
    app_secret_key: str = Field(default="dev-secret-key-dev-secret-key-32", alias="APP_SECRET_KEY")
    admin_password: str = Field(default="dev-admin-password", alias="ADMIN_PASSWORD")
    database_url: str = Field(default="sqlite:///./youziloadlab.dev.db", alias="DATABASE_URL")
    data_dir: str = Field(default="./data", alias="DATA_DIR")
    runner_workdir: str = Field(default="./data/runs", alias="RUNNER_WORKDIR")
    max_concurrent_runs: int = Field(default=1, alias="MAX_CONCURRENT_RUNS")
    max_users_per_run: int = Field(default=200, alias="MAX_USERS_PER_RUN")
    allow_public_runs: bool = Field(default=False, alias="ALLOW_PUBLIC_RUNS")
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:8000", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

Create `apps/api/youziloadlab_api/core/time.py`:

```python
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def utc_now_iso() -> str:
    return utc_now().isoformat()
```

- [ ] **Step 4: Implement app and health route**

Create `apps/api/youziloadlab_api/modules/health/router.py`:

```python
from fastapi import APIRouter

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.core.time import utc_now_iso

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "timestamp": utc_now_iso(),
    }
```

Create `apps/api/youziloadlab_api/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.modules.health.router import router as health_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api")
    return app


app = create_app()
```

- [ ] **Step 5: Run test to verify pass**

Run: `pytest apps/api/tests/test_health.py -q`
Expected: `1 passed`.

- [ ] **Step 6: Commit**

Run:

```powershell
git add apps/api/youziloadlab_api apps/api/tests/test_health.py
git commit -m "feat(api): add settings and health endpoint"
```

---

### Task 3: Secret Encryption and Redaction

**Files:**
- Create: `apps/api/youziloadlab_api/core/security.py`
- Create: `apps/api/tests/test_security.py`

- [ ] **Step 1: Write failing security tests**

Create `apps/api/tests/test_security.py`:

```python
from youziloadlab_api.core.security import SecretBox, mask_secret, redact_sensitive_text, secret_fingerprint


def test_secret_box_encrypts_and_decrypts_without_plaintext_leak() -> None:
    box = SecretBox("test-secret-key-test-secret-key-32")
    plaintext = "sk-live-secret-value"
    ciphertext = box.encrypt(plaintext)
    assert plaintext not in ciphertext
    assert box.decrypt(ciphertext) == plaintext


def test_secret_fingerprint_is_stable_and_short() -> None:
    assert secret_fingerprint("sk-live-secret-value") == secret_fingerprint("sk-live-secret-value")
    assert len(secret_fingerprint("sk-live-secret-value")) == 10


def test_mask_secret_keeps_only_edges() -> None:
    assert mask_secret("sk-1234567890abcdef") == "sk-1...cdef"
    assert mask_secret("short") == "*****"


def test_redact_sensitive_text_removes_keys_tokens_and_cookies() -> None:
    raw = "Authorization: Bearer sk-secret123 Cookie: session=abc fk-fireworks-secret"
    redacted = redact_sensitive_text(raw)
    assert "sk-secret123" not in redacted
    assert "session=abc" not in redacted
    assert "fk-fireworks-secret" not in redacted
    assert "[REDACTED_BEARER]" in redacted
    assert "[REDACTED_COOKIE]" in redacted
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/api/tests/test_security.py -q`
Expected: fail because `security.py` does not exist yet.

- [ ] **Step 3: Implement security helpers**

Create `apps/api/youziloadlab_api/core/security.py`:

```python
import base64
import hashlib
import re
from dataclasses import dataclass

from cryptography.fernet import Fernet

_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE)
_COOKIE_RE = re.compile(r"Cookie:\s*[^\n\r]+", re.IGNORECASE)
_SK_RE = re.compile(r"sk-[A-Za-z0-9_\-]{6,}")
_FK_RE = re.compile(r"fk-[A-Za-z0-9_\-]{6,}")


def _fernet_key_from_secret(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@dataclass(frozen=True)
class SecretBox:
    app_secret_key: str

    def encrypt(self, plaintext: str) -> str:
        token = Fernet(_fernet_key_from_secret(self.app_secret_key)).encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        plaintext = Fernet(_fernet_key_from_secret(self.app_secret_key)).decrypt(ciphertext.encode("utf-8"))
        return plaintext.decode("utf-8")


def secret_fingerprint(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:10]


def mask_secret(secret: str) -> str:
    if len(secret) < 12:
        return "*****"
    return f"{secret[:4]}...{secret[-4:]}"


def redact_sensitive_text(text: str) -> str:
    redacted = _BEARER_RE.sub("Bearer [REDACTED_BEARER]", text)
    redacted = _COOKIE_RE.sub("Cookie: [REDACTED_COOKIE]", redacted)
    redacted = _SK_RE.sub("sk-[REDACTED]", redacted)
    redacted = _FK_RE.sub("fk-[REDACTED]", redacted)
    return redacted
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest apps/api/tests/test_security.py -q`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

Run:

```powershell
git add apps/api/youziloadlab_api/core/security.py apps/api/tests/test_security.py
git commit -m "feat(api): add encrypted secret utilities"
```

---

### Task 4: Database Models and Session Lifecycle

**Files:**
- Create: `apps/api/youziloadlab_api/db/__init__.py`
- Create: `apps/api/youziloadlab_api/db/models.py`
- Create: `apps/api/youziloadlab_api/db/session.py`
- Create: `apps/api/tests/test_db_models.py`

- [ ] **Step 1: Write failing database test**

Create `apps/api/tests/test_db_models.py`:

```python
from sqlmodel import Session, SQLModel, create_engine, select

from youziloadlab_api.db.models import Target


def test_target_model_round_trips() -> None:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        target = Target(
            name="local nashiyard",
            kind="nashiyard",
            base_url="http://localhost:3000",
            admin_username="root",
            default_model="gpt-4o-mini",
        )
        session.add(target)
        session.commit()
        saved = session.exec(select(Target).where(Target.name == "local nashiyard")).one()
    assert saved.id
    assert saved.kind == "nashiyard"
    assert saved.base_url == "http://localhost:3000"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/api/tests/test_db_models.py -q`
Expected: fail because `youziloadlab_api.db.models` does not exist.

- [ ] **Step 3: Implement SQLModel models**

Create empty `apps/api/youziloadlab_api/db/__init__.py`.

Create `apps/api/youziloadlab_api/db/models.py`:

```python
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
```

- [ ] **Step 4: Implement session helpers**

Create `apps/api/youziloadlab_api/db/session.py`:

```python
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from youziloadlab_api.core.config import get_settings


def create_db_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = create_db_engine()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

- [ ] **Step 5: Run tests and commit**

Run: `pytest apps/api/tests/test_db_models.py apps/api/tests/test_health.py apps/api/tests/test_security.py -q`
Expected: `6 passed`.

Run:

```powershell
git add apps/api/youziloadlab_api/db apps/api/tests/test_db_models.py
git commit -m "feat(api): add database models and session helpers"
```

---

### Task 5: Targets API

**Files:**
- Create: `apps/api/youziloadlab_api/schemas/target.py`
- Create: `apps/api/youziloadlab_api/services/target_service.py`
- Create: `apps/api/youziloadlab_api/modules/targets/router.py`
- Modify: `apps/api/youziloadlab_api/main.py`
- Create: `apps/api/tests/test_targets.py`

- [ ] **Step 1: Write failing target API test**

Create `apps/api/tests/test_targets.py`:

```python
from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_create_and_list_targets() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/targets",
        json={
            "name": "local nashiyard",
            "kind": "nashiyard",
            "base_url": "http://localhost:3000/",
            "admin_username": "root",
            "default_model": "gpt-4o-mini",
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["base_url"] == "http://localhost:3000"

    list_response = client.get("/api/targets")
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "local nashiyard"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/api/tests/test_targets.py -q`
Expected: fail with 404 for `/api/targets`.

- [ ] **Step 3: Implement target schemas**

Create `apps/api/youziloadlab_api/schemas/target.py`:

```python
from pydantic import BaseModel, Field, field_validator


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: str = Field(pattern="^(nashiyard|openai_compatible|generic_http)$")
    base_url: str = Field(min_length=1, max_length=500)
    admin_username: str | None = Field(default=None, max_length=120)
    default_model: str | None = Field(default=None, max_length=200)

    @field_validator("base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        return value.rstrip("/")


class TargetRead(BaseModel):
    id: str
    name: str
    kind: str
    base_url: str
    admin_username: str | None
    default_model: str | None
```

- [ ] **Step 4: Implement service and router**

Create `apps/api/youziloadlab_api/services/target_service.py`:

```python
from sqlmodel import Session, select

from youziloadlab_api.db.models import Target
from youziloadlab_api.schemas.target import TargetCreate


def create_target(session: Session, data: TargetCreate) -> Target:
    target = Target(**data.model_dump())
    session.add(target)
    session.commit()
    session.refresh(target)
    return target


def list_targets(session: Session) -> list[Target]:
    return list(session.exec(select(Target).order_by(Target.created_at.desc())).all())
```

Create `apps/api/youziloadlab_api/modules/targets/router.py`:

```python
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from youziloadlab_api.db.session import get_session, init_db
from youziloadlab_api.schemas.target import TargetCreate, TargetRead
from youziloadlab_api.services.target_service import create_target, list_targets

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post("", response_model=TargetRead, status_code=status.HTTP_201_CREATED)
def create_target_endpoint(payload: TargetCreate, session: Session = Depends(get_session)):
    init_db()
    return create_target(session, payload)


@router.get("", response_model=list[TargetRead])
def list_targets_endpoint(session: Session = Depends(get_session)):
    init_db()
    return list_targets(session)
```

Modify `apps/api/youziloadlab_api/main.py` to include:

```python
from youziloadlab_api.modules.targets.router import router as targets_router
```

and inside `create_app()` after health router:

```python
app.include_router(targets_router, prefix="/api")
```

- [ ] **Step 5: Run test and commit**

Run: `pytest apps/api/tests/test_targets.py -q`
Expected: `1 passed`.

Run:

```powershell
git add apps/api/youziloadlab_api apps/api/tests/test_targets.py
git commit -m "feat(api): add targets api"
```

---

### Task 6: Secrets API with Encrypted Storage

**Files:**
- Create: `apps/api/youziloadlab_api/schemas/secret.py`
- Create: `apps/api/youziloadlab_api/services/secret_service.py`
- Create: `apps/api/youziloadlab_api/modules/secrets/router.py`
- Modify: `apps/api/youziloadlab_api/main.py`
- Create: `apps/api/tests/test_secrets.py`

- [ ] **Step 1: Write failing secret API test**

Create `apps/api/tests/test_secrets.py`:

```python
from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_secret_create_list_never_returns_plaintext() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/secrets",
        json={"name": "admin password", "kind": "admin_password", "plaintext": "super-secret-value"},
    )
    assert response.status_code == 201
    created = response.json()
    assert "plaintext" not in created
    assert "ciphertext" not in created
    assert created["masked"] == "supe...alue"
    assert len(created["fingerprint"]) == 10

    list_response = client.get("/api/secrets")
    assert list_response.status_code == 200
    assert "super-secret-value" not in list_response.text
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/api/tests/test_secrets.py -q`
Expected: fail with 404 for `/api/secrets`.

- [ ] **Step 3: Implement secret schemas/service/router**

Create `apps/api/youziloadlab_api/schemas/secret.py`:

```python
from pydantic import BaseModel, Field


class SecretCreate(BaseModel):
    target_id: str | None = None
    name: str = Field(min_length=1, max_length=120)
    kind: str = Field(pattern="^(api_key|admin_password|fireworks_keys|bearer_token|cookie)$")
    plaintext: str = Field(min_length=1)


class SecretRead(BaseModel):
    id: str
    target_id: str | None
    name: str
    kind: str
    fingerprint: str
    masked: str
```

Create `apps/api/youziloadlab_api/services/secret_service.py`:

```python
from sqlmodel import Session, select

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.core.security import SecretBox, mask_secret, secret_fingerprint
from youziloadlab_api.db.models import Secret
from youziloadlab_api.schemas.secret import SecretCreate, SecretRead


def _read_model(secret: Secret, plaintext: str | None = None) -> SecretRead:
    masked = mask_secret(plaintext) if plaintext is not None else "********"
    return SecretRead(
        id=secret.id,
        target_id=secret.target_id,
        name=secret.name,
        kind=secret.kind,
        fingerprint=secret.fingerprint,
        masked=masked,
    )


def create_secret(session: Session, data: SecretCreate) -> SecretRead:
    box = SecretBox(get_settings().app_secret_key)
    secret = Secret(
        target_id=data.target_id,
        name=data.name,
        kind=data.kind,
        ciphertext=box.encrypt(data.plaintext),
        fingerprint=secret_fingerprint(data.plaintext),
    )
    session.add(secret)
    session.commit()
    session.refresh(secret)
    return _read_model(secret, data.plaintext)


def list_secrets(session: Session) -> list[SecretRead]:
    rows = session.exec(select(Secret).order_by(Secret.created_at.desc())).all()
    return [_read_model(row) for row in rows]
```

Create `apps/api/youziloadlab_api/modules/secrets/router.py`:

```python
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from youziloadlab_api.db.session import get_session, init_db
from youziloadlab_api.schemas.secret import SecretCreate, SecretRead
from youziloadlab_api.services.secret_service import create_secret, list_secrets

router = APIRouter(prefix="/secrets", tags=["secrets"])


@router.post("", response_model=SecretRead, status_code=status.HTTP_201_CREATED)
def create_secret_endpoint(payload: SecretCreate, session: Session = Depends(get_session)):
    init_db()
    return create_secret(session, payload)


@router.get("", response_model=list[SecretRead])
def list_secrets_endpoint(session: Session = Depends(get_session)):
    init_db()
    return list_secrets(session)
```

Modify `apps/api/youziloadlab_api/main.py` to include secrets router.

- [ ] **Step 4: Run test and commit**

Run: `pytest apps/api/tests/test_secrets.py -q`
Expected: `1 passed`.

Run:

```powershell
git add apps/api/youziloadlab_api apps/api/tests/test_secrets.py
git commit -m "feat(api): add encrypted secrets api"
```

---

### Task 7: Scenario Registry API

**Files:**
- Create: `apps/api/youziloadlab_api/schemas/scenario.py`
- Create: `apps/api/youziloadlab_api/services/scenario_registry.py`
- Create: `apps/api/youziloadlab_api/modules/scenarios/router.py`
- Modify: `apps/api/youziloadlab_api/main.py`
- Create: `apps/api/tests/test_scenarios.py`

- [ ] **Step 1: Write failing scenario registry test**

Create `apps/api/tests/test_scenarios.py`:

```python
from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_scenarios_include_v1_core_suites() -> None:
    client = TestClient(create_app())
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert "openai-chat-load" in ids
    assert "nashiyard-fireworks-channel" in ids
    assert "nashiyard-polling-system" in ids
    assert "smoke-check" in ids
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/api/tests/test_scenarios.py -q`
Expected: fail with 404 for `/api/scenarios`.

- [ ] **Step 3: Implement registry**

Create `apps/api/youziloadlab_api/schemas/scenario.py`:

```python
from pydantic import BaseModel


class ScenarioRead(BaseModel):
    id: str
    title: str
    description: str
    version: str
    schema_json: dict
    enabled: bool
```

Create `apps/api/youziloadlab_api/services/scenario_registry.py`:

```python
CORE_SCENARIOS: list[dict] = [
    {
        "id": "openai-chat-load",
        "title": "OpenAI-Compatible Chat Load",
        "description": "Generic /v1/chat/completions pressure test for OpenAI-compatible gateways.",
        "version": "0.1.0",
        "schema_json": {"type": "object", "required": ["request", "loadProfile"]},
        "enabled": True,
    },
    {
        "id": "nashiyard-fireworks-channel",
        "title": "NashiYard Fireworks Channel Stress",
        "description": "Creates isolated NashiYard test users/tokens/channels and stresses Fireworks routing.",
        "version": "0.1.0",
        "schema_json": {"type": "object", "required": ["setup", "request", "loadProfile", "cleanup"]},
        "enabled": True,
    },
    {
        "id": "nashiyard-polling-system",
        "title": "NashiYard Polling System Stress",
        "description": "Stresses polling-style admin/background workflows and their interaction with API traffic.",
        "version": "0.1.0",
        "schema_json": {"type": "object", "required": ["polling", "loadProfile"]},
        "enabled": True,
    },
    {
        "id": "smoke-check",
        "title": "Smoke Check",
        "description": "Short preflight run for auth, model availability, token usability, and sanitization checks.",
        "version": "0.1.0",
        "schema_json": {"type": "object", "required": ["targetId"]},
        "enabled": True,
    },
]


def list_core_scenarios() -> list[dict]:
    return CORE_SCENARIOS
```

Create `apps/api/youziloadlab_api/modules/scenarios/router.py`:

```python
from fastapi import APIRouter

from youziloadlab_api.schemas.scenario import ScenarioRead
from youziloadlab_api.services.scenario_registry import list_core_scenarios

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioRead])
def list_scenarios_endpoint():
    return list_core_scenarios()
```

Modify `apps/api/youziloadlab_api/main.py` to include scenarios router.

- [ ] **Step 4: Run test and commit**

Run: `pytest apps/api/tests/test_scenarios.py -q`
Expected: `1 passed`.

Run:

```powershell
git add apps/api/youziloadlab_api apps/api/tests/test_scenarios.py
git commit -m "feat(api): add scenario registry"
```

---

### Task 8: Runner Contracts, Payload Builder, and Metrics Aggregation

**Files:**
- Create: `runner/youziloadlab_runner/__init__.py`
- Create: `runner/youziloadlab_runner/contracts.py`
- Create: `runner/youziloadlab_runner/payloads.py`
- Create: `runner/youziloadlab_runner/metrics.py`
- Create: `runner/tests/test_payloads.py`
- Create: `runner/tests/test_metrics.py`

- [ ] **Step 1: Write failing runner tests**

Create `runner/tests/test_payloads.py`:

```python
from youziloadlab_runner.payloads import build_chat_payload


def test_build_chat_payload_supports_stream_flag() -> None:
    payload = build_chat_payload(
        model="accounts/fireworks/models/llama-v3p1-8b-instruct",
        prompt="Say hello",
        max_tokens=64,
        temperature=0.2,
        stream=True,
    )
    assert payload["model"] == "accounts/fireworks/models/llama-v3p1-8b-instruct"
    assert payload["messages"] == [{"role": "user", "content": "Say hello"}]
    assert payload["max_tokens"] == 64
    assert payload["temperature"] == 0.2
    assert payload["stream"] is True
```

Create `runner/tests/test_metrics.py`:

```python
from youziloadlab_runner.metrics import ErrorClassifier, percentile


def test_percentile_uses_nearest_rank() -> None:
    assert percentile([10, 20, 30, 40, 50], 95) == 50
    assert percentile([10, 20, 30, 40, 50], 50) == 30


def test_error_classifier_handles_nashiyard_and_provider_errors() -> None:
    classifier = ErrorClassifier()
    assert classifier.classify(429, "rate limit") == "rate_limited"
    assert classifier.classify(412, "invalid key") == "fireworks_412"
    assert classifier.classify(500, "upstream failed") == "upstream_5xx"
    assert classifier.classify(0, "timeout") == "timeout"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest runner/tests -q`
Expected: fail because `youziloadlab_runner` does not exist.

- [ ] **Step 3: Implement runner contracts and helpers**

Create empty `runner/youziloadlab_runner/__init__.py`.

Create `runner/youziloadlab_runner/contracts.py`:

```python
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
```

Create `runner/youziloadlab_runner/payloads.py`:

```python
def build_chat_payload(
    *, model: str, prompt: str, max_tokens: int, temperature: float, stream: bool
) -> dict:
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }
```

Create `runner/youziloadlab_runner/metrics.py`:

```python
import math


def percentile(values: list[float], percent: int) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    rank = math.ceil((percent / 100) * len(ordered))
    return ordered[max(rank - 1, 0)]


class ErrorClassifier:
    def classify(self, status_code: int, body: str) -> str:
        lowered = body.lower()
        if status_code == 0 or "timeout" in lowered:
            return "timeout"
        if status_code == 412:
            return "fireworks_412"
        if status_code == 429:
            return "rate_limited"
        if status_code in {401, 402, 403}:
            return "auth_or_quota"
        if 500 <= status_code <= 599:
            return "upstream_5xx"
        return "other_error"
```

- [ ] **Step 4: Run tests and commit**

Run: `pytest runner/tests/test_payloads.py runner/tests/test_metrics.py -q`
Expected: `4 passed`.

Run:

```powershell
git add runner/youziloadlab_runner runner/tests
git commit -m "feat(runner): add contracts payloads and metrics"
```

---

### Task 9: NashiYard Admin Adapter

**Files:**
- Create: `runner/youziloadlab_runner/adapters/nashiyard_admin.py`
- Create: `runner/tests/test_nashiyard_admin.py`

- [ ] **Step 1: Write failing adapter tests with mocked transport**

Create `runner/tests/test_nashiyard_admin.py`:

```python
import httpx

from youziloadlab_runner.adapters.nashiyard_admin import NashiYardAdminClient


def test_admin_client_login_posts_expected_payload() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"success": True})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")
    admin = NashiYardAdminClient(base_url="http://test", username="root", password="secret", client=client)

    assert admin.login() is True
    assert requests[0].url.path == "/api/user/login"
    assert b"root" in requests[0].content


def test_admin_client_builds_test_user_payload_with_discord_exempt() -> None:
    admin = NashiYardAdminClient(base_url="http://test", username="root", password="secret")
    payload = admin.build_create_user_payload("stress_test_fw_001", "Passw0rd!", "fireworks_stress")
    assert payload["username"] == "stress_test_fw_001"
    assert payload["group"] == "fireworks_stress"
    assert payload["discord_gate_exempt"] is True
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest runner/tests/test_nashiyard_admin.py -q`
Expected: fail because adapter does not exist.

- [ ] **Step 3: Implement adapter**

Create `runner/youziloadlab_runner/adapters/nashiyard_admin.py`:

```python
import httpx


class NashiYardAdminClient:
    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = client or httpx.Client(base_url=self.base_url, timeout=30)

    def login(self) -> bool:
        response = self.client.post(
            "/api/user/login",
            json={"username": self.username, "password": self.password},
        )
        return response.status_code == 200 and response.json().get("success") is True

    def build_create_user_payload(self, username: str, password: str, group: str) -> dict:
        return {
            "username": username,
            "password": password,
            "group": group,
            "discord_gate_exempt": True,
        }

    def create_user(self, username: str, password: str, group: str) -> bool:
        response = self.client.post(
            "/api/user/",
            json=self.build_create_user_payload(username, password, group),
        )
        return response.status_code in {200, 201}
```

- [ ] **Step 4: Run tests and commit**

Run: `pytest runner/tests/test_nashiyard_admin.py -q`
Expected: `2 passed`.

Run:

```powershell
git add runner/youziloadlab_runner/adapters/nashiyard_admin.py runner/tests/test_nashiyard_admin.py
git commit -m "feat(runner): add nashiyard admin adapter"
```

---

### Task 10: OpenAI-Compatible Locust Scenario

**Files:**
- Create: `runner/youziloadlab_runner/scenarios/openai_chat_load.py`
- Create: `runner/tests/test_openai_chat_scenario.py`

- [ ] **Step 1: Write failing scenario test**

Create `runner/tests/test_openai_chat_scenario.py`:

```python
from youziloadlab_runner.scenarios.openai_chat_load import build_headers, should_stream


def test_build_headers_uses_bearer_token() -> None:
    assert build_headers("sk-test") == {
        "Authorization": "Bearer sk-test",
        "Content-Type": "application/json",
    }


def test_should_stream_respects_ratio_edges() -> None:
    assert should_stream(0.0, random_value=0.0) is False
    assert should_stream(1.0, random_value=0.99) is True
    assert should_stream(0.25, random_value=0.20) is True
    assert should_stream(0.25, random_value=0.30) is False
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest runner/tests/test_openai_chat_scenario.py -q`
Expected: fail because scenario does not exist.

- [ ] **Step 3: Implement reusable scenario helpers**

Create `runner/youziloadlab_runner/scenarios/openai_chat_load.py`:

```python
import random

from locust import HttpUser, between, task

from youziloadlab_runner.payloads import build_chat_payload


def build_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def should_stream(stream_ratio: float, *, random_value: float | None = None) -> bool:
    value = random.random() if random_value is None else random_value
    return value < stream_ratio


class OpenAIChatUser(HttpUser):
    wait_time = between(0.1, 1.0)

    @task
    def chat_completion(self) -> None:
        token = self.environment.parsed_options.token
        model = self.environment.parsed_options.model
        prompt = self.environment.parsed_options.prompt
        max_tokens = int(self.environment.parsed_options.max_tokens)
        temperature = float(self.environment.parsed_options.temperature)
        stream_ratio = float(self.environment.parsed_options.stream_ratio)
        stream = should_stream(stream_ratio)
        self.client.post(
            "/v1/chat/completions",
            headers=build_headers(token),
            json=build_chat_payload(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream,
            ),
            name="POST /v1/chat/completions",
        )
```

- [ ] **Step 4: Run tests and commit**

Run: `pytest runner/tests/test_openai_chat_scenario.py -q`
Expected: `2 passed`.

Run:

```powershell
git add runner/youziloadlab_runner/scenarios/openai_chat_load.py runner/tests/test_openai_chat_scenario.py
git commit -m "feat(runner): add openai chat locust scenario"
```

---

### Task 11: Run Creation API and Locust Process Wrapper

**Files:**
- Create: `apps/api/youziloadlab_api/schemas/run.py`
- Create: `apps/api/youziloadlab_api/services/locust_process.py`
- Create: `apps/api/youziloadlab_api/services/run_orchestrator.py`
- Create: `apps/api/youziloadlab_api/modules/runs/router.py`
- Modify: `apps/api/youziloadlab_api/main.py`
- Create: `apps/api/tests/test_runs.py`

- [ ] **Step 1: Write failing runs API test**

Create `apps/api/tests/test_runs.py`:

```python
from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_create_run_starts_in_created_state() -> None:
    client = TestClient(create_app())
    target = client.post(
        "/api/targets",
        json={"name": "openai compat", "kind": "openai_compatible", "base_url": "http://localhost:3000"},
    ).json()
    response = client.post(
        "/api/runs",
        json={
            "name": "baseline chat",
            "target_id": target["id"],
            "scenario_id": "openai-chat-load",
            "config_json": {"request": {"model": "gpt-4o-mini"}, "loadProfile": {"phases": []}},
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "created"
    assert body["scenario_id"] == "openai-chat-load"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/api/tests/test_runs.py -q`
Expected: fail with 404 for `/api/runs`.

- [ ] **Step 3: Implement run schemas and orchestrator**

Create `apps/api/youziloadlab_api/schemas/run.py`:

```python
from pydantic import BaseModel, Field


class RunCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    target_id: str
    scenario_id: str
    config_json: dict


class RunRead(BaseModel):
    id: str
    name: str
    target_id: str
    scenario_id: str
    status: str
    config_json: dict
    locust_web_url: str | None
    error_message: str | None
```

Create `apps/api/youziloadlab_api/services/locust_process.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class LocustLaunchResult:
    web_url: str
    pid: int | None


class LocustProcessManager:
    def launch_placeholder(self, run_id: str) -> LocustLaunchResult:
        return LocustLaunchResult(web_url=f"/locust/{run_id}", pid=None)
```

Create `apps/api/youziloadlab_api/services/run_orchestrator.py`:

```python
from sqlmodel import Session, select

from youziloadlab_api.db.models import Run
from youziloadlab_api.schemas.run import RunCreate


def create_run(session: Session, payload: RunCreate) -> Run:
    run = Run(**payload.model_dump(), status="created")
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def list_runs(session: Session) -> list[Run]:
    return list(session.exec(select(Run).order_by(Run.created_at.desc())).all())
```

Create `apps/api/youziloadlab_api/modules/runs/router.py`:

```python
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from youziloadlab_api.db.session import get_session, init_db
from youziloadlab_api.schemas.run import RunCreate, RunRead
from youziloadlab_api.services.run_orchestrator import create_run, list_runs

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run_endpoint(payload: RunCreate, session: Session = Depends(get_session)):
    init_db()
    return create_run(session, payload)


@router.get("", response_model=list[RunRead])
def list_runs_endpoint(session: Session = Depends(get_session)):
    init_db()
    return list_runs(session)
```

Modify `apps/api/youziloadlab_api/main.py` to include runs router.

- [ ] **Step 4: Run tests and commit**

Run: `pytest apps/api/tests/test_runs.py -q`
Expected: `1 passed`.

Run:

```powershell
git add apps/api/youziloadlab_api apps/api/tests/test_runs.py
git commit -m "feat(api): add run creation api"
```

---

### Task 12: Report Generation Service

**Files:**
- Create: `apps/api/youziloadlab_api/schemas/report.py`
- Create: `apps/api/youziloadlab_api/services/report_service.py`
- Create: `apps/api/youziloadlab_api/modules/reports/router.py`
- Modify: `apps/api/youziloadlab_api/main.py`
- Create: `apps/api/tests/test_reports.py`

- [ ] **Step 1: Write failing report service test**

Create `apps/api/tests/test_reports.py`:

```python
from youziloadlab_api.services.report_service import render_markdown_report


def test_render_markdown_report_contains_summary_and_redacts_secrets() -> None:
    markdown = render_markdown_report(
        run_name="baseline",
        scenario_id="openai-chat-load",
        summary={"requests_total": 10, "failures_total": 1, "p95_latency_ms": 123.4},
        notes="Authorization: Bearer sk-secret123",
    )
    assert "# YouziLoadLab Run Report" in markdown
    assert "baseline" in markdown
    assert "openai-chat-load" in markdown
    assert "requests_total" in markdown
    assert "sk-secret123" not in markdown
    assert "[REDACTED_BEARER]" in markdown
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/api/tests/test_reports.py -q`
Expected: fail because `report_service.py` does not exist.

- [ ] **Step 3: Implement report service and route**

Create `apps/api/youziloadlab_api/schemas/report.py`:

```python
from pydantic import BaseModel


class ReportRead(BaseModel):
    id: str
    run_id: str
    summary_json: dict
    markdown: str
```

Create `apps/api/youziloadlab_api/services/report_service.py`:

```python
import json

from youziloadlab_api.core.security import redact_sensitive_text
from youziloadlab_api.core.time import utc_now_iso


def render_markdown_report(*, run_name: str, scenario_id: str, summary: dict, notes: str) -> str:
    safe_notes = redact_sensitive_text(notes)
    safe_summary = redact_sensitive_text(json.dumps(summary, ensure_ascii=False, indent=2))
    return f"""# YouziLoadLab Run Report

Generated at: {utc_now_iso()}

## Run

- Name: {run_name}
- Scenario: {scenario_id}

## Summary

```json
{safe_summary}
```

## Notes

{safe_notes}
"""
```

Create `apps/api/youziloadlab_api/modules/reports/router.py`:

```python
from fastapi import APIRouter

from youziloadlab_api.services.report_service import render_markdown_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/preview")
def preview_report() -> dict[str, str]:
    return {
        "markdown": render_markdown_report(
            run_name="preview",
            scenario_id="smoke-check",
            summary={"requests_total": 0, "failures_total": 0},
            notes="preview",
        )
    }
```

Modify `apps/api/youziloadlab_api/main.py` to include reports router.

- [ ] **Step 4: Run tests and commit**

Run: `pytest apps/api/tests/test_reports.py -q`
Expected: `1 passed`.

Run:

```powershell
git add apps/api/youziloadlab_api apps/api/tests/test_reports.py
git commit -m "feat(api): add report rendering"
```

---

### Task 13: React WebUI Skeleton

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/index.html`
- Create: `apps/web/vite.config.ts`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/src/main.tsx`
- Create: `apps/web/src/App.tsx`
- Create: `apps/web/src/api/client.ts`
- Create: `apps/web/src/types/api.ts`
- Create: `apps/web/src/pages/DashboardPage.tsx`

- [ ] **Step 1: Create Web package**

Create `apps/web/package.json`:

```json
{
  "name": "@youziloadlab/web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc && vite build",
    "typecheck": "tsc --noEmit",
    "test": "vitest run"
  },
  "dependencies": {
    "@emotion/react": "^11.13.0",
    "@emotion/styled": "^11.13.0",
    "@mui/icons-material": "^6.1.0",
    "@mui/material": "^6.1.0",
    "@vitejs/plugin-react": "^4.3.1",
    "recharts": "^2.12.7",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vite": "^5.4.0",
    "vitest": "^2.1.0"
  }
}
```

- [ ] **Step 2: Create Vite config and HTML**

Create `apps/web/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>YouziLoadLab</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `apps/web/vite.config.ts`:

```ts
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
```

Create `apps/web/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create API types and client**

Create `apps/web/src/types/api.ts`:

```ts
export type HealthResponse = {
  status: string;
  app: string;
  environment: string;
  timestamp: string;
};
```

Create `apps/web/src/api/client.ts`:

```ts
import type { HealthResponse } from '../types/api';

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/health');
  if (!response.ok) {
    throw new Error(`Health request failed: ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}
```

- [ ] **Step 4: Create dashboard app**

Create `apps/web/src/pages/DashboardPage.tsx`:

```tsx
import { Box, Card, CardContent, Chip, Typography } from '@mui/material';

export function DashboardPage() {
  return (
    <Box sx={{ p: 4, display: 'grid', gap: 2 }}>
      <Typography variant="h4" fontWeight={700}>YouziLoadLab</Typography>
      <Typography color="text.secondary">
        WebUI load testing for NashiYard and OpenAI-compatible API gateways.
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="h6">V1 Scenario Suites</Typography>
          <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
            <Chip label="OpenAI Chat Load" color="primary" />
            <Chip label="NashiYard Fireworks" color="secondary" />
            <Chip label="Polling System" />
            <Chip label="Smoke Check" />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
```

Create `apps/web/src/App.tsx`:

```tsx
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';

import { DashboardPage } from './pages/DashboardPage';

const theme = createTheme({ palette: { mode: 'light' } });

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <DashboardPage />
    </ThemeProvider>
  );
}
```

Create `apps/web/src/main.tsx`:

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 5: Run Web build and commit**

Run:

```powershell
pnpm install
pnpm --filter @youziloadlab/web build
```

Expected: Vite build succeeds and emits `apps/web/dist`.

Run:

```powershell
git add apps/web package.json pnpm-workspace.yaml
git commit -m "feat(web): add dashboard skeleton"
```

---

### Task 14: Docker and Zeabur Deployment

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `zeabur.json`
- Create: `docs/deployment-zeabur.md`

- [ ] **Step 1: Create Dockerfile**

Create `Dockerfile`:

```dockerfile
FROM node:22-alpine AS web
WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN corepack enable && pnpm install --frozen-lockfile=false
COPY apps/web apps/web
RUN pnpm --filter @youziloadlab/web build

FROM python:3.12-slim AS api
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY pyproject.toml README.md ./
COPY apps/api apps/api
COPY runner runner
RUN pip install --no-cache-dir -e .
COPY --from=web /app/apps/web/dist apps/api/youziloadlab_api/static
EXPOSE 8000
CMD ["uvicorn", "youziloadlab_api.main:app", "--app-dir", "apps/api", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create docker-compose for local validation**

Create `docker-compose.yml`:

```yaml
services:
  youziloadlab:
    build: .
    ports:
      - "8000:8000"
    environment:
      APP_ENV: development
      APP_SECRET_KEY: dev-secret-key-dev-secret-key-32
      ADMIN_PASSWORD: dev-admin-password
      DATABASE_URL: sqlite:////data/youziloadlab.db
      DATA_DIR: /data
      RUNNER_WORKDIR: /data/runs
    volumes:
      - ./data:/data
```

- [ ] **Step 3: Create Zeabur config and docs**

Create `zeabur.json`:

```json
{
  "name": "youziloadlab",
  "framework": "dockerfile",
  "port": 8000
}
```

Create `docs/deployment-zeabur.md`:

```markdown
# Zeabur Deployment

## Required Environment Variables

- `APP_ENV=production`
- `APP_SECRET_KEY=<32+ character secret>`
- `ADMIN_PASSWORD=<operator password>`
- `DATABASE_URL=sqlite:////data/youziloadlab.db`
- `DATA_DIR=/data`
- `RUNNER_WORKDIR=/data/runs`
- `MAX_CONCURRENT_RUNS=1`
- `MAX_USERS_PER_RUN=200`

## Volume

Mount a persistent volume at `/data`.

## Health Check

After deployment, open:

```text
https://<your-zeabur-domain>/api/health
```

Expected response contains `"status":"ok"`.
```

- [ ] **Step 4: Build Docker image and commit**

Run: `docker build -t youziloadlab .`
Expected: image builds successfully.

Run:

```powershell
git add Dockerfile docker-compose.yml zeabur.json docs/deployment-zeabur.md
git commit -m "chore: add docker and zeabur deployment"
```

---

### Task 15: Full Validation Gate

**Files:**
- Modify: `README.md`
- Create: `docs/validation.md`

- [ ] **Step 1: Create validation doc**

Create `docs/validation.md`:

```markdown
# Validation Checklist

Run these commands before marking V1 implementation complete.

```powershell
pytest apps/api/tests runner/tests -q
python -m ruff check apps/api runner
python -m mypy apps/api runner
pnpm --filter @youziloadlab/web typecheck
pnpm --filter @youziloadlab/web build
docker build -t youziloadlab .
```

Expected results:

- pytest passes.
- ruff reports no errors.
- mypy reports no errors.
- TypeScript typecheck passes.
- Vite build succeeds.
- Docker image builds.
```

- [ ] **Step 2: Add validation link to README**

Append to `README.md`:

```markdown
## Validation

See `docs/validation.md` for the full pre-release validation checklist.
```

- [ ] **Step 3: Run full validation and commit**

Run all commands from `docs/validation.md`.
Expected: all pass.

Run:

```powershell
git add README.md docs/validation.md
git commit -m "docs: add validation checklist"
```

---

## Self-Review

### Spec coverage

- WebUI project: Task 13 creates the React/MUI skeleton and sets the path for subsequent pages.
- Zeabur deployment: Task 14 creates Docker and Zeabur configuration.
- Locust engine: Tasks 8, 10, and 11 create runner contracts, a Locust scenario, and process wrapper foundation.
- NashiYard-specific setup: Task 9 creates the admin adapter; scenario-specific expansion is detailed in the scenarios plan.
- Secret handling: Task 3 and Task 6 cover encryption, masking, and no-plaintext API responses.
- Strong first version: Tasks cover targets, secrets, scenarios, runs, reports, WebUI, Docker, and validation rather than a toy script.

### Placeholder scan

This plan avoids `TBD`, `TODO`, vague error handling instructions, and undefined future references. Scenario deep details are intentionally placed in the separate scenarios plan, not omitted.

### Type consistency

Route names, scenario IDs, model names, and config fields are consistent with `2026-05-05-youziloadlab-architecture.md`.
