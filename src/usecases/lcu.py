from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select

from src.database.connection import get_session
from src.database.models import (
    Account,
    Champion,
    ChampionShard,
    Collection,
    Credentials,
    Loot,
    Rank,
    RankedQueue,
    Skin,
    SkinShard,
    Summoner,
    Verification,
)
from src.lcu.auto_accept import auto_accept_service
from src.lcu.client import (
    clear_challenges_preferences,
    dodge_champ_select,
    get_current_account,
    set_current_summoner_icon,
)


def account_summary(account: Account) -> dict:
    summoner = account.summoner
    rank = account.rank
    ranked_queues = []
    if rank:
        for queue in rank.ranked_queues:
            ranked_queues.append({
                "type": queue.type,
                "tier": queue.tier,
                "division": queue.division,
                "league_points": queue.league_points,
                "wins": queue.wins,
                "losses": queue.losses,
                "days_until_decay": queue.days_until_decay,
                "decay_deadline": _format_datetime(queue.decay_deadline),
            })
    
    return {
        "id": account.id,
        "summoner": {
            "name": summoner.name if summoner else None,
            "tag": summoner.tag if summoner else None,
            "region": summoner.region if summoner else None,
            "level": summoner.level if summoner else None,
            "icon_url": summoner.icon_url if summoner else None,
        },
        "rank": {"ranked_queues": ranked_queues} if ranked_queues else None,
    }


def get_auto_accept_status() -> dict:
    return auto_accept_service.status()


def start_auto_accept() -> dict:
    started = auto_accept_service.start()
    return {
        "status": "started" if started else "already_running",
        **auto_accept_service.status(),
    }


def stop_auto_accept() -> dict:
    stopped = auto_accept_service.stop()
    return {
        "status": "stopped" if stopped else "already_stopped",
        **auto_accept_service.status(),
    }


def get_current_account_from_lcu() -> dict:
    payload = get_current_account()
    if not payload:
        raise RuntimeError("League Client not available")
    return payload


def clear_challenges() -> dict:
    result = clear_challenges_preferences()
    if not result:
        raise RuntimeError("League Client not available")
    
    if not result.get("ok"):
        raise RuntimeError(
            f"Failed to clear challenges preferences (status {result.get('status')})"
        )
    
    return {"status": "ok", "lcu_status": result.get("status")}


def set_summoner_icon(icon_id: int) -> dict:
    if icon_id < 0:
        raise ValueError("icon_id must be greater than or equal to 0")
    
    result = set_current_summoner_icon(icon_id)
    if not result:
        raise RuntimeError("League Client not available")
    
    if not result.get("ok"):
        raise RuntimeError(
            f"Failed to set summoner icon (status {result.get('status')})"
        )
    
    return {"status": "ok", "lcu_status": result.get("status")}


def dodge_lobby() -> dict:
    result = dodge_champ_select()
    if not result:
        raise RuntimeError("League Client not available")
    
    if not result.get("ok"):
        raise RuntimeError(
            f"Failed to dodge champ select (status {result.get('status')})"
        )
    
    return {"status": "ok", "lcu_status": result.get("status")}


def current_account_exists() -> dict:
    payload = get_current_account_from_lcu()
    summoner = payload.get("summoner") or {}
    puuid = summoner.get("puuid")
    if not puuid:
        raise ValueError("Missing summoner PUUID")
    
    with get_session() as session:
        existing_summoner = session.execute(
            select(Summoner).where(Summoner.puuid == puuid)
        ).scalar_one_or_none()
        if not existing_summoner or not existing_summoner.account:
            return {"exists": False}
        
        account = existing_summoner.account
        
        return {"exists": True, "account": account_summary(account)}


def save_current_account(
    login: str | None = None,
    password: str | None = None,
    overwrite: bool = False,
) -> dict:
    current = get_current_account_from_lcu()
    summoner = current.get("summoner") or {}
    puuid = summoner.get("puuid")
    if not puuid:
        raise ValueError("Missing summoner PUUID")

    with get_session() as session:
        existing_summoner = session.execute(
            select(Summoner).where(Summoner.puuid == puuid)
        ).scalar_one_or_none()

        existing_account = existing_summoner.account if existing_summoner else None
        existing_credentials = existing_account.credentials if existing_account else None

        if existing_account and not overwrite:
            summary = account_summary(existing_account)
            raise RuntimeError(f"Account already exists: {summary}")

        if existing_account:
            existing_notes = existing_account.notes
            session.delete(existing_account)
            session.flush()
        else:
            existing_notes = ""

        account = Account(notes=existing_notes)

        resolved_login = existing_credentials.login if existing_credentials else login
        resolved_password = (
            existing_credentials.password if existing_credentials else password
        )
        if resolved_login is None:
            resolved_login = "Undefined"
    
        if resolved_password is None:
            resolved_password = "Undefined"

        account.credentials = Credentials(
            login=resolved_login,
            password=resolved_password,
        )

        verification = current.get("verification") or {}
        account.verification = Verification(
            email=verification.get("email") or "unknown",
            phone=verification.get("phone"),
            is_email_verified=bool(verification.get("is_email_verified")),
            is_phone_verified=bool(verification.get("is_phone_verified")),
        )

        account.summoner = Summoner(
            summoner_account_id=summoner.get("summoner_account_id"),
            summoner_id=summoner.get("summoner_id"),
            puuid=summoner.get("puuid"),
            region=summoner.get("region"),
            name=summoner.get("name"),
            tag=summoner.get("tag"),
            level=summoner.get("level"),
            icon_id=summoner.get("icon_id"),
            icon_url=summoner.get("icon_url"),
        )

        rank_payload = current.get("rank")
        if rank_payload:
            rank = Rank()
            for queue in rank_payload.get("ranked_queues", []):
                rank.ranked_queues.append(
                    RankedQueue(
                        type=queue.get("type"),
                        tier=queue.get("tier"),
                        division=queue.get("division"),
                        league_points=queue.get("league_points", 0),
                        wins=queue.get("wins", 0),
                        losses=queue.get("losses", 0),
                        days_until_decay=queue.get("days_until_decay"),
                        decay_deadline=_decay_deadline_for_queue(queue),
                    )
                )
            account.rank = rank

        collection_payload = current.get("collection")
        if collection_payload:
            collection = Collection()
            for champ in collection_payload.get("champions", []):
                collection.champions.append(
                    Champion(
                        champion_id=champ.get("champion_id"),
                        alias=champ.get("alias"),
                        name=champ.get("name"),
                        purchased=champ.get("purchased"),
                    )
                )
            for skin in collection_payload.get("skins", []):
                collection.skins.append(
                    Skin(
                        skin_id=skin.get("skin_id"),
                        name=skin.get("name"),
                        description=skin.get("description"),
                        purchased=skin.get("purchased"),
                    )
                )
            account.collection = collection

        loot_payload = current.get("loot")
        if loot_payload:
            loot = Loot(
                blue_essence=loot_payload.get("blue_essence", 0),
                orange_essence=loot_payload.get("orange_essence", 0),
                riot_points=loot_payload.get("riot_points", 0),
                keys=loot_payload.get("keys", 0),
                key_fragments=loot_payload.get("key_fragments", 0),
                chests=loot_payload.get("chests", 0),
                champion_mastery_chests=loot_payload.get("champion_mastery_chests", 0),
            )
            for shard in loot_payload.get("champion_shards", []):
                loot.champion_shards.append(
                    ChampionShard(
                        type=shard.get("type"),
                        name=shard.get("name"),
                        amount=shard.get("amount", 0),
                        disenchant_value=shard.get("disenchant_value", 0),
                        upgrade_essence_value=shard.get("upgrade_essence_value", 0),
                        is_already_owned=bool(shard.get("is_already_owned")),
                    )
                )
            for shard in loot_payload.get("skin_shards", []):
                loot.skin_shards.append(
                    SkinShard(
                        type=shard.get("type"),
                        name=shard.get("name"),
                        amount=shard.get("amount", 0),
                        disenchant_value=shard.get("disenchant_value", 0),
                        upgrade_essence_value=shard.get("upgrade_essence_value", 0),
                        is_already_owned=bool(shard.get("is_already_owned")),
                    )
                )
            account.loot = loot

        session.add(account)
        session.commit()
        session.refresh(account)

    return {"status": "saved", "account_id": account.id}


def _decay_deadline_for_queue(queue: dict) -> datetime | None:
    days_until_decay = queue.get("days_until_decay")
    if days_until_decay is None:
        return None

    try:
        days = int(days_until_decay)
    except (TypeError, ValueError):
        return None

    now = datetime.now().astimezone()
    local_midnight = datetime.combine(
        now.date() + timedelta(days=max(days, 0)),
        time.min,
        tzinfo=now.tzinfo,
    )
    return local_midnight.astimezone(timezone.utc)


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat()
