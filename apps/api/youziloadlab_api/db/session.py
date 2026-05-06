from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from youziloadlab_api.core.config import get_settings


def create_db_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = create_db_engine()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_sqlite_run_columns(engine)


def _ensure_sqlite_run_columns(db_engine: Engine) -> None:
    if not db_engine.url.drivername.startswith("sqlite"):
        return
    columns = {
        "pid": "INTEGER",
        "workdir": "VARCHAR(1000)",
        "command_json": "JSON DEFAULT '[]'",
        "artifacts_json": "JSON DEFAULT '{}'",
        "exit_code": "INTEGER",
    }
    with db_engine.begin() as connection:
        existing = {
            str(row[1])
            for row in connection.execute(text("PRAGMA table_info(runs)")).fetchall()
        }
        for column_name, column_type in columns.items():
            if column_name not in existing:
                connection.execute(text(f"ALTER TABLE runs ADD COLUMN {column_name} {column_type}"))


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
