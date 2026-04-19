from __future__ import annotations

from sqlalchemy import text

from src.database.connection import get_session
from src.lcu.client import get_current_account


def check_communitydragon() -> dict:
    return {"ok": True, "status": 200}


def check_lcu() -> dict:
    try:
        payload = get_current_account()
        return {"ok": bool(payload)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def check_database() -> dict:
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def health() -> dict:
    return {
        "communitydragon": check_communitydragon(),
        "lcu": check_lcu(),
        "database": check_database(),
    }
