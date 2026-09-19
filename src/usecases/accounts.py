from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database.connection import get_session
from src.database.models import Account, Collection, Credentials, Loot, Rank


def _account_query():
    return (
        select(Account)
        .options(
            selectinload(Account.credentials),
            selectinload(Account.verification),
            selectinload(Account.summoner),
            selectinload(Account.rank).selectinload(Rank.ranked_queues),
            selectinload(Account.collection).selectinload(Collection.champions),
            selectinload(Account.collection).selectinload(Collection.skins),
            selectinload(Account.loot).selectinload(Loot.champion_shards),
            selectinload(Account.loot).selectinload(Loot.skin_shards),
        )
    )


def account_to_payload(account: Account) -> dict:
    return {
        "id": account.id,
        "notes": account.notes,
        "credentials": {
            "login": account.credentials.login,
            "password": account.credentials.password,
        }
        if account.credentials
        else None,
        "verification": {
            "email": account.verification.email,
            "is_email_verified": bool(account.verification.is_email_verified),
            "phone": account.verification.phone,
            "is_phone_verified": bool(account.verification.is_phone_verified),
        }
        if account.verification
        else None,
        "summoner": {
            "summoner_account_id": account.summoner.summoner_account_id,
            "summoner_id": account.summoner.summoner_id,
            "puuid": account.summoner.puuid,
            "region": account.summoner.region,
            "name": account.summoner.name,
            "tag": account.summoner.tag,
            "level": account.summoner.level,
            "icon_id": account.summoner.icon_id,
            "icon_url": account.summoner.icon_url,
        }
        if account.summoner
        else None,
        "rank": {
            "ranked_queues": [
                {
                    "type": rq.type,
                    "tier": rq.tier,
                    "division": rq.division,
                    "league_points": rq.league_points,
                    "wins": rq.wins,
                    "losses": rq.losses,
                    "days_until_decay": rq.days_until_decay,
                    "decay_deadline": _format_datetime(rq.decay_deadline),
                }
                for rq in account.rank.ranked_queues
            ]
        }
        if account.rank
        else None,
        "collection": {
            "champions": [
                {
                    "champion_id": champ.champion_id,
                    "alias": champ.alias,
                    "name": champ.name,
                    "purchased": champ.purchased,
                }
                for champ in account.collection.champions
            ],
            "skins": [
                {
                    "skin_id": skin.skin_id,
                    "name": skin.name,
                    "description": skin.description,
                    "purchased": skin.purchased,
                }
                for skin in account.collection.skins
            ],
        }
        if account.collection
        else None,
        "loot": {
            "blue_essence": account.loot.blue_essence,
            "orange_essence": account.loot.orange_essence,
            "riot_points": account.loot.riot_points,
            "keys": account.loot.keys,
            "key_fragments": account.loot.key_fragments,
            "chests": account.loot.chests,
            "champion_shards": [
                {
                    "type": shard.type,
                    "name": shard.name,
                    "amount": shard.amount,
                    "disenchant_value": shard.disenchant_value,
                    "upgrade_essence_value": shard.upgrade_essence_value,
                    "is_already_owned": bool(shard.is_already_owned),
                }
                for shard in account.loot.champion_shards
            ],
            "skin_shards": [
                {
                    "type": shard.type,
                    "name": shard.name,
                    "amount": shard.amount,
                    "disenchant_value": shard.disenchant_value,
                    "upgrade_essence_value": shard.upgrade_essence_value,
                    "is_already_owned": bool(shard.is_already_owned),
                }
                for shard in account.loot.skin_shards
            ],
        }
        if account.loot
        else None,
    }


def list_accounts() -> list[dict]:
    with get_session() as session:
        result = session.execute(_account_query().order_by(Account.id))
        return [account_to_payload(account) for account in result.scalars().all()]


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat()


def get_account(account_id: int) -> dict:
    with get_session() as session:
        account = session.execute(
            _account_query().where(Account.id == account_id)
        ).scalar_one_or_none()
        if not account:
            raise LookupError("Account not found")
        return account_to_payload(account)


def update_account_credentials(account_id: int, login: str, password: str) -> dict:
    with get_session() as session:
        account = session.execute(
            select(Account).where(Account.id == account_id)
        ).scalar_one_or_none()
        if not account:
            raise LookupError("Account not found")
        
        if account.credentials is None:
            account.credentials = Credentials(login=login, password=password)
        else:
            account.credentials.login = login
            account.credentials.password = password
        
        session.add(account)
        session.commit()
        session.refresh(account)
        return account_to_payload(account)


def update_account_notes(account_id: int, notes: str) -> dict:
    with get_session() as session:
        account = session.execute(
            select(Account).where(Account.id == account_id)
        ).scalar_one_or_none()
        if not account:
            raise LookupError("Account not found")

        account.notes = notes
        session.commit()
        session.refresh(account)
        return account_to_payload(account)


def delete_account(account_id: int) -> dict:
    with get_session() as session:
        account = session.execute(
            select(Account).where(Account.id == account_id)
        ).scalar_one_or_none()
        if not account:
            raise LookupError("Account not found")
        session.delete(account)
        session.commit()
        return {"status": "deleted", "account_id": account_id}
