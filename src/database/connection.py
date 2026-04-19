from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
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
    Base.metadata.create_all(bind=engine)


SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


def get_session() -> Session:
    return SessionLocal()
