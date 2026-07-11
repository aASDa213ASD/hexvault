from __future__ import annotations

import json
import ssl
import urllib.request
from functools import lru_cache
from typing import Any

from src.datadragon.endpoints import Endpoint


def get_image_url(lol_game_data_path: str | None) -> str | None:
    if not lol_game_data_path:
        return None
    path = lol_game_data_path.lower().replace("/lol-game-data/assets/", "")
    return f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/{path}"


def get_icon_url(icon_id: int | None) -> str | None:
    if icon_id is None:
        return None
    return (
        "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/"
        f"global/default/v1/profile-icons/{icon_id}.jpg"
    )


def get_rank_icon_url(tier: str) -> str:
    return (
        "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/"
        f"global/default/images/ranked-mini-crests/{tier}.svg"
    )


def _fetch_json(url: str) -> Any:
    if hasattr(url, "value"):
        url = url.value
    context = ssl._create_unverified_context()
    req = urllib.request.Request(
        url=url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(req, context=context, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


@lru_cache(maxsize=1)
def get_skins_map() -> dict:
    try:
        data = _fetch_json(Endpoint.SKINS)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}
    return {}


@lru_cache(maxsize=1)
def get_champions_map() -> dict:
    try:
        data = _fetch_json(Endpoint.CHAMPIONS)
        if isinstance(data, list):
            return {
                champion["id"]: champion
                for champion in data
                if isinstance(champion, dict) and "id" in champion
            }
    except Exception:
        return {}
    return {}
