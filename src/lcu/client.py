from __future__ import annotations

import base64
import json
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.datadragon.client import (
    get_icon_url,
    get_image_url,
    get_rank_icon_url,
    get_skins_map,
)
from src.lcu.endpoints import Endpoint

PLACEHOLDER_ACCOUNT_IMAGE_URL = (
    "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/assets/rewards/honor/milestone/images/honor_background_5.png"
)
APEX_RANK_TIERS = {
    "MASTER",
    "GRANDMASTER",
    "CHALLENGER"
}


@dataclass
class LcuConfig:
    base_url: str
    password: str


def _read_lockfile() -> LcuConfig | None:
    base_path = os.getenv("LEAGUE_OF_LEGENDS_PATH")
    if not base_path:
        return None
    lockfile = Path(base_path) / "lockfile"
    if not lockfile.exists():
        return None
    payload = lockfile.read_text(encoding="utf-8").strip()
    parts = payload.split(":")
    if len(parts) < 5:
        return None
    port = parts[2]
    password = parts[3]
    protocol = parts[4]
    return LcuConfig(base_url=f"{protocol}://127.0.0.1:{port}", password=password)


def _request(config: LcuConfig, path: str) -> Any:
    if hasattr(path, "value"):
        path = path.value

    auth = base64.b64encode(f"riot:{config.password}".encode("utf-8")).decode("ascii")
    req = urllib.request.Request(
        url=f"{config.base_url}{path}",
        headers={"Authorization": f"Basic {auth}"},
    )
    context = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(req, context=context, timeout=2) as response:
            data = response.read()
        return json.loads(data.decode("utf-8"))
    except Exception as exc:
        print("LCU request failed:", path, exc)
        return None



def _request_json(
    config: LcuConfig, method: str, path: str, payload: dict | None = None
) -> tuple[int | None, Any]:
    if hasattr(path, "value"):
        path = path.value

    auth = base64.b64encode(f"riot:{config.password}".encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {auth}"}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        url=f"{config.base_url}{path}",
        headers=headers,
        data=body,
        method=method.upper(),
    )

    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=context, timeout=2) as response:
            data = response.read()
            status = response.status
        if not data:
            return status, None
        return status, json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body_data = exc.read().decode("utf-8")
            parsed = json.loads(body_data) if body_data else None
        except Exception:
            parsed = None
        return exc.code, parsed
    except Exception as exc:
        print("LCU request failed:", path, exc)
        return None, None


def _parse_rank_tier(value: str | None) -> str:
    return (value or "UNRANKED").strip().title()


def _parse_rank_division(tier: str, value: str | None) -> str | None:
    normalized_tier = tier.strip().upper()
    normalized_value = (value or "").strip().upper()
    
    if normalized_tier == "UNRANKED":
        return None
    
    if normalized_tier in APEX_RANK_TIERS:
        return "I"
    
    if not normalized_value or normalized_value == "NA":
        return None
    
    return normalized_value


def clear_challenges_preferences() -> dict | None:
    config = _read_lockfile()
    if not config:
        return None

    status, payload = _request_json(
        config,
        "POST",
        Endpoint.CHALLENGES_PLAYER_PREFERENCES,
        {"challengeIds": []},
    )
    if status is None:
        return None
    
    return {
        "status": status,
        "ok": status in (200, 201, 204),
        "payload": payload
    }


def set_current_summoner_icon(profile_icon_id: int) -> dict | None:
    config = _read_lockfile()
    if not config:
        return None

    status, payload = _request_json(
        config,
        "PUT",
        Endpoint.CURRENT_SUMMONER_ICON,
        {"profileIconId": profile_icon_id},
    )
    if status is None:
        return None

    return {
        "status": status,
        "ok": status in (200, 201, 204),
        "payload": payload
    }


def get_matchmaking_search_state() -> str | None:
    config = _read_lockfile()
    if not config:
        return None
    
    payload = _request(config, Endpoint.MATCHMAKING_SEARCH_STATE)
    if not isinstance(payload, dict):
        return None
    
    value = payload.get("searchState")
    return value if isinstance(value, str) else None


def is_match_found() -> bool:
    return get_matchmaking_search_state() == "Found"


def is_match_searching() -> bool:
    return get_matchmaking_search_state() == "Searching"


def accept_ready_check() -> dict | None:
    config = _read_lockfile()
    if not config:
        return None

    status, payload = _request_json(
        config,
        "POST",
        Endpoint.READY_CHECK_ACCEPT,
    )
    if status is None:
        return None

    return {
        "status": status,
        "ok": status in (200, 201, 204),
        "payload": payload
    }


def dodge_champ_select() -> dict | None:
    config = _read_lockfile()
    if not config:
        return None

    status, payload = _request_json(
        config,
        "POST",
        Endpoint.DODGE_CHAMP_SELECT,
        {},
    )
    if status is None:
        return None
    return {
        "status": status,
        "ok": status in (200, 201, 204),
        "payload": payload
    }


def get_current_account() -> dict | None:
    config = _read_lockfile()
    if not config:
        return None

    current = _request(config, Endpoint.CURRENT_SUMMONER)
    region_data = _request(config, Endpoint.CURRENT_REGION)
    if not current or not region_data:
        return None

    summoner = {
        "summoner_account_id": current.get("accountId"),
        "summoner_id": current.get("summonerId"),
        "puuid": current.get("puuid"),
        "region": region_data.get("region"),
        "name": current.get("gameName"),
        "tag": current.get("tagLine"),
        "level": current.get("summonerLevel"),
        "icon_id": current.get("profileIconId"),
        "icon_url": get_icon_url(current.get("profileIconId")),
    }

    verification_data = _request(config, Endpoint.EMAIL_VERIFICATION) or {}
    verification = {
        "email": verification_data.get("email"),
        "is_email_verified": bool(verification_data.get("emailVerified", False)),
        "phone": None,
        "is_phone_verified": False,
    }

    rank_payload = _request(config, Endpoint.CURRENT_RANK) or {}
    queues = []
    queue_map = rank_payload.get("queueMap") if isinstance(rank_payload, dict) else None
    if queue_map:
        for queue_type in ("RANKED_SOLO_5x5", "RANKED_FLEX_SR"):
            data = queue_map.get(queue_type, {})
            tier = _parse_rank_tier(data.get("tier"))
            division = _parse_rank_division(tier, data.get("division"))
            queues.append(
                {
                    "type": queue_type,
                    "tier": tier,
                    "division": division,
                    "league_points": data.get("leaguePoints", 0),
                    "wins": data.get("wins", 0),
                    "losses": data.get("losses", 0),
                    "icon_url": get_rank_icon_url(tier.lower()),
                }
            )

    collection = _build_collection(config)
    loot = _build_loot(config)

    return {
        "account_image_url": PLACEHOLDER_ACCOUNT_IMAGE_URL,
        "summoner": summoner,
        "verification": verification,
        "rank": {"ranked_queues": queues} if queues else None,
        "collection": collection,
        "loot": loot,
    }

def get_current_summoner() -> dict | None:
    config = _read_lockfile()
    if not config:
        return None

    current = _request(config, Endpoint.CURRENT_SUMMONER)
    if not current:
        return None

    summoner = {
        "name": current.get("gameName"),
        "tag": current.get("tagLine"),
        "level": current.get("summonerLevel"),
        "icon_id": current.get("profileIconId"),
        "icon_url": get_icon_url(current.get("profileIconId")),
    }

    return summoner

def _build_collection(config: LcuConfig) -> dict:
    champions = []
    owned_champions = _request(config, Endpoint.OWNED_CHAMPIONS) or []
    for champ in owned_champions:
        ownership = champ.get("ownership") or {}
        if not ownership.get("owned"):
            continue
        champions.append(
            {
                "champion_id": champ.get("id"),
                "alias": champ.get("alias"),
                "name": champ.get("name"),
                "title": champ.get("title"),
                "image_url": get_image_url(champ.get("squarePortraitPath")),
                "splash_url": get_image_url(champ.get("baseSplashPath")),
            }
        )

    skins = []
    owned_skins = _request(config, Endpoint.OWNED_SKINS) or []
    skins_map = get_skins_map()
    for skin in owned_skins:
        item_id = skin.get("itemId")
        meta = skins_map.get(str(item_id))
        if not meta:
            continue
        name = meta.get("name")
        tile_path = meta.get("tilePath")
        if not name or not tile_path:
            continue
        skins.append(
            {
                "skin_id": item_id,
                "name": name,
                "description": meta.get("description"),
                "image_url": get_image_url(tile_path),
            }
        )

    return {"champions": champions, "skins": skins}


def _build_loot(config: LcuConfig) -> dict | None:
    wallet = _request(config, Endpoint.CURRENT_WALLET) or {}
    if not wallet:
        return None
    loot = {
        "blue_essence": wallet.get("lol_blue_essence", 0),
        "orange_essence": wallet.get("lol_orange_essence", 0),
        "riot_points": wallet.get("RP", 0),
        "champion_shards": [],
        "skin_shards": [],
    }

    owned_loot = _request(config, Endpoint.OWNED_LOOT) or []
    for shard in owned_loot:
        shard_type = shard.get("type")
        if shard_type not in ("CHAMPION_RENTAL", "CHAMPION", "SKIN_RENTAL", "SKIN"):
            continue
        payload = {
            "type": shard_type,
            "name": shard.get("itemDesc"),
            "amount": shard.get("count", 0),
            "disenchant_value": shard.get("disenchantValue", 0),
            "upgrade_essence_value": shard.get("upgradeEssenceValue", 0),
            "is_already_owned": shard.get("itemStatus") == "OWNED",
            "image_url": get_image_url(shard.get("tilePath")),
        }
        if shard_type in ("CHAMPION_RENTAL", "CHAMPION"):
            loot["champion_shards"].append(payload)
        else:
            loot["skin_shards"].append(payload)

    return loot
