from __future__ import annotations

import psutil
import base64
import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.datadragon.client import (
    get_icon_url,
    get_skins_map,
    get_champions_map,
)

from src.lcu.endpoints import Endpoint


APEX_RANK_TIERS = {
    "MASTER",
    "GRANDMASTER",
    "CHALLENGER"
}
RIOT_CLIENT_PROCESSES = {
    "riot client.exe",
    "riotclientservices.exe",
}
LEAGUE_CLIENT_PROCESS = "leagueclientux.exe"


@dataclass
class LCUConfig:
    base_url: str
    password: str


@dataclass
class LCUProcessConfig:
    league_client: LCUConfig | None
    riot_client: LCUConfig | None
    region: str | None = None


def _read_lcu_process_config() -> LCUProcessConfig | None:
    league_client: LCUConfig | None = None
    riot_client: LCUConfig | None = None
    region: str | None = None

    for process in psutil.process_iter(["name", "cmdline"]):
        try:
            process_name = (process.info.get("name") or "").lower()
            if process_name not in {LEAGUE_CLIENT_PROCESS, *RIOT_CLIENT_PROCESSES}:
                continue

            args = process.info.get("cmdline") or []
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue

        values = _parse_process_args(args)
        region = region or (values.get("region") or "").lower() or None

        if process_name == LEAGUE_CLIENT_PROCESS and league_client is None:
            league_client = _config_from_values(
                values,
                port_key="app-port",
                password_key="remoting-auth-token",
            )

        if riot_client is None:
            if process_name == LEAGUE_CLIENT_PROCESS:
                riot_client = _config_from_values(
                    values,
                    port_key="riotclient-app-port",
                    password_key="riotclient-auth-token",
                )
            else:
                riot_client = _config_from_values(
                    values,
                    port_key="app-port",
                    password_key="remoting-auth-token",
                ) or _config_from_values(
                    values,
                    port_key="riotclient-app-port",
                    password_key="riotclient-auth-token",
                )

    if league_client or riot_client:
        return LCUProcessConfig(
            league_client=league_client,
            riot_client=riot_client,
            region=region,
        )

    return None


def _parse_process_args(args: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for arg in args:
        if not arg.startswith("--") or "=" not in arg:
            continue
        key, value = arg[2:].split("=", 1)
        values[key] = value
    return values


def _config_from_values(
    values: dict[str, str],
    *,
    port_key: str,
    password_key: str,
) -> LCUConfig | None:
    port = values.get(port_key)
    password = values.get(password_key)
    if not port or not password:
        return None
    
    return LCUConfig(
        base_url=f"https://127.0.0.1:{port}",
        password=password,
    )


def _read_lcu_process() -> LCUConfig | None:
    config = _read_lcu_process_config()
    return config.league_client if config else None


def get_lcu_config() -> LCUConfig | None:
    return _read_lcu_process()


def get_riot_client_config() -> LCUConfig | None:
    config = _read_lcu_process_config()
    return config.riot_client if config else None


def get_lcu_process_config() -> LCUProcessConfig | None:
    return _read_lcu_process_config()


def _request(config: LCUConfig, path: str | Endpoint) -> Any:
    if isinstance(path, Endpoint):
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
    config: LCUConfig,
    method: str,
    path: str | Endpoint,
    payload: dict | None = None,
) -> tuple[int | None, Any]:
    if isinstance(path, Endpoint):
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


def _format_lcu_timestamp(value: int | float | str | None) -> str | None:
    if value in (None, ""):
        return None
    
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        
        for date_format in ("%Y%m%dT%H%M%S.%fZ", "%Y%m%dT%H%M%SZ"):
            try:
                parsed = datetime.strptime(normalized, date_format)
                return parsed.replace(tzinfo=timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
            except ValueError:
                pass
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return None
    
    if timestamp <= 0:
        return None
    
    if timestamp > 10_000_000_000:
        timestamp /= 1000
    
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def clear_challenges_preferences() -> dict | None:
    config = _read_lcu_process()
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
    config = _read_lcu_process()
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
    config = _read_lcu_process()
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
    config = _read_lcu_process()
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
    config = _read_lcu_process()
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
    config = _read_lcu_process()
    if not config:
        return None

    current = _request(config, Endpoint.CURRENT_SUMMONER)
    riot_config = get_riot_client_config()
    region_data = _request(riot_config or config, Endpoint.CURRENT_REGION)
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
            warnings = data.get("warnings") or {}
            queues.append({
                "type": queue_type,
                "tier": tier,
                "division": division,
                "league_points": data.get("leaguePoints", 0),
                "wins": data.get("wins", 0),
                "losses": data.get("losses", 0),
                "days_until_decay": warnings.get("daysUntilDecay"),
            })

    collection = _build_collection(config)
    loot = _build_loot(config)

    return {
        "summoner": summoner,
        "verification": verification,
        "rank": {"ranked_queues": queues} if queues else None,
        "collection": collection,
        "loot": loot,
    }

def get_current_summoner() -> dict | None:
    config = _read_lcu_process()
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

def _build_collection(config: LCUConfig) -> dict:
    champions = []
    champions_owned = _request(config, Endpoint.OWNED_CHAMPIONS) or []
    champions_map = get_champions_map()
    for champion in champions_owned:
        ownership = champion.get("ownership") or {}
        if not ownership.get("owned"):
            continue
        champion_id = champion.get("id")
        meta = champions_map.get(champion_id) or champion

        champions.append({
            "champion_id": champion_id,
            "alias": meta.get("alias"),
            "name": meta.get("name"),
            "purchased": _format_lcu_timestamp(champion.get("purchased")),
        })

    skins = []
    owned_skins = _request(config, Endpoint.OWNED_SKINS) or []
    skins_map = get_skins_map()
    for skin in owned_skins:
        item_id = skin.get("itemId")
        meta = skins_map.get(str(item_id))
        if not meta:
            continue

        name = meta.get("name")
        if not name:
            continue

        skins.append({
            "skin_id": item_id,
            "name": name,
            "description": meta.get("description"),
            "purchased": _format_lcu_timestamp(skin.get("purchaseDate")),
        })

    return {"champions": champions, "skins": skins}


def _build_loot(config: LCUConfig) -> dict | None:
    wallet = _request(config, Endpoint.CURRENT_WALLET) or {}
    if not wallet:
        return None

    loot = {
        "blue_essence": wallet.get("lol_blue_essence", 0),
        "orange_essence": wallet.get("lol_orange_essence", 0),
        "riot_points": wallet.get("RP", 0),
        "keys": 0,
        "key_fragments": 0,
        "chests": 0,
        "champion_shards": [],
        "skin_shards": [],
    }

    owned_loot = _request(config, Endpoint.OWNED_LOOT) or []
    champions_map = get_champions_map()
    skins_map = get_skins_map()
    for shard in owned_loot:
        loot_id = shard.get("lootId")
        material_field = {
            "MATERIAL_key": "keys",
            "MATERIAL_key_fragment": "key_fragments",
            "CHEST_generic": "chests",
        }.get(loot_id)
        if material_field:
            loot[material_field] += shard.get("count", 0)
            continue

        shard_type = shard.get("type")
        if shard_type not in ("CHAMPION_RENTAL", "CHAMPION", "SKIN_RENTAL", "SKIN"):
            continue

        item_id = shard.get("itemId")
        if item_id is None:
            item_id = shard.get("storeItemId")
        if shard_type in ("CHAMPION_RENTAL", "CHAMPION"):
            try:
                champion_id = int(item_id)
            except (TypeError, ValueError):
                champion_id = item_id
            meta = champions_map.get(champion_id) or {}
        else:
            meta = skins_map.get(str(item_id)) or {}

        name = meta.get("name")
        if not name:
            continue

        payload = {
            "type": shard_type,
            "name": name,
            "amount": shard.get("count", 0),
            "disenchant_value": shard.get("disenchantValue", 0),
            "upgrade_essence_value": shard.get("upgradeEssenceValue", 0),
            "is_already_owned": shard.get("itemStatus") == "OWNED",
        }
        
        if shard_type in ("CHAMPION_RENTAL", "CHAMPION"):
            loot["champion_shards"].append(payload)
        else:
            loot["skin_shards"].append(payload)

    return loot
