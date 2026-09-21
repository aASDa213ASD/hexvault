from __future__ import annotations

import json
from pathlib import Path

from src.ui.shared.theme import DEFAULT_THEME_NAME, THEME_COLORS


SETTINGS_PATH = Path(__file__).resolve().parents[3] / "var" / "settings.json"


def load_theme_name() -> str:
    try:
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return DEFAULT_THEME_NAME

    if not isinstance(settings, dict):
        return DEFAULT_THEME_NAME
    theme_name = settings.get("theme")
    return theme_name if theme_name in THEME_COLORS else DEFAULT_THEME_NAME


def save_theme_name(theme_name: str) -> None:
    if theme_name not in THEME_COLORS:
        raise ValueError(f"Unknown theme: {theme_name}")

    settings: dict = {}
    try:
        loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            settings = loaded
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    settings["theme"] = theme_name
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = SETTINGS_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(settings, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(SETTINGS_PATH)
