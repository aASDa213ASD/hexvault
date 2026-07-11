from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base

REPO_ROOT = Path(__file__).resolve().parents[2]
VAR_DIR = REPO_ROOT / "var"
DEFAULT_DB_PATH = VAR_DIR / "accounts.db"


def get_db_path() -> Path:
    override = os.getenv("DATABASE_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_DB_PATH


def get_engine():
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", future=True)


def init_db() -> None:
    engine = get_engine()
    try:
        run_migrations(engine)
        Base.metadata.create_all(bind=engine)
    finally:
        engine.dispose()


def run_migrations(engine: Engine) -> None:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        if _has_unversioned_schema(connection):
            command.stamp(config, "0001")
        command.upgrade(config, "head")


def _has_unversioned_schema(connection) -> bool:
    inspector = inspect(connection)
    table_names = set(inspector.get_table_names())
    app_tables = {name for name in table_names if not name.startswith("sqlite_")}
    return bool(app_tables) and "alembic_version" not in table_names


SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


def get_session() -> Session:
    return SessionLocal()
