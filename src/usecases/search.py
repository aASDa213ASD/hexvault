from __future__ import annotations

import operator
import re
from typing import Any

from src.usecases.accounts import list_accounts
from src.usecases.datadragon import RANK_TIERS


FIELD_PATHS = {
    "account.id": "id",
    "account.notes": "notes",
    "credentials.login": "credentials.login",
    "credentials.password": "credentials.password",
    "verification.email": "verification.email",
    "verification.phone": "verification.phone",
    "verification.is_email_verified": "verification.is_email_verified",
    "verification.is_phone_verified": "verification.is_phone_verified",
    "summoner.summoner_account_id": "summoner.summoner_account_id",
    "summoner.summoner_id": "summoner.summoner_id",
    "summoner.puuid": "summoner.puuid",
    "summoner.region": "summoner.region",
    "summoner.name": "summoner.name",
    "summoner.tag": "summoner.tag",
    "summoner.level": "summoner.level",
    "summoner.icon_id": "summoner.icon_id",
    "summoner.icon_url": "summoner.icon_url",
    "ranked_queues.type": "rank.ranked_queues.type",
    "ranked_queues.tier": "rank.ranked_queues.tier",
    "ranked_queues.division": "rank.ranked_queues.division",
    "ranked_queues.league_points": "rank.ranked_queues.league_points",
    "ranked_queues.wins": "rank.ranked_queues.wins",
    "ranked_queues.losses": "rank.ranked_queues.losses",
    "ranked_queues.days_until_decay": "rank.ranked_queues.days_until_decay",
    "ranked_queues.decay_deadline": "rank.ranked_queues.decay_deadline",
    "champions.champion_id": "collection.champions.champion_id",
    "champions.alias": "collection.champions.alias",
    "champions.name": "collection.champions.name",
    "champions.purchased": "collection.champions.purchased",
    "skins.skin_id": "collection.skins.skin_id",
    "skins.name": "collection.skins.name",
    "skins.description": "collection.skins.description",
    "skins.purchased": "collection.skins.purchased",
    "loot.blue_essence": "loot.blue_essence",
    "loot.orange_essence": "loot.orange_essence",
    "loot.riot_points": "loot.riot_points",
    "loot.keys": "loot.keys",
    "loot.key_fragments": "loot.key_fragments",
    "loot.chests": "loot.chests",
    "loot.champion_mastery_chests": "loot.champion_mastery_chests",
    "champion_shards.type": "loot.champion_shards.type",
    "champion_shards.name": "loot.champion_shards.name",
    "champion_shards.amount": "loot.champion_shards.amount",
    "champion_shards.disenchant_value": "loot.champion_shards.disenchant_value",
    "champion_shards.upgrade_essence_value": "loot.champion_shards.upgrade_essence_value",
    "champion_shards.is_already_owned": "loot.champion_shards.is_already_owned",
    "skin_shards.type": "loot.skin_shards.type",
    "skin_shards.name": "loot.skin_shards.name",
    "skin_shards.amount": "loot.skin_shards.amount",
    "skin_shards.disenchant_value": "loot.skin_shards.disenchant_value",
    "skin_shards.upgrade_essence_value": "loot.skin_shards.upgrade_essence_value",
    "skin_shards.is_already_owned": "loot.skin_shards.is_already_owned",
}

EXPRESSION = re.compile(r"^([a-zA-Z0-9_.]+)\s*(>=|<=|!=|=|>|<|~)\s*(.*?)\s*$")


def search_accounts(filters: dict[str, Any]) -> list[dict]:
    predicates = _common_predicates(filters)
    predicates.extend(_advanced_predicates(filters.get("advanced", "")))
    return [account for account in list_accounts() if all(test(account) for test in predicates)]


def _common_predicates(filters: dict[str, Any]) -> list:
    predicates = []
    region = str(filters.get("region") or "").strip().casefold()
    if region:
        predicates.append(lambda account: region == str(_one(account, "summoner.region") or "").casefold())

    rank_min = str(filters.get("rank_min") or "").strip().upper()
    rank_max = str(filters.get("rank_max") or "").strip().upper()
    if rank_min or rank_max:
        lower = RANK_TIERS.index(rank_min) if rank_min else 0
        upper = RANK_TIERS.index(rank_max) if rank_max else len(RANK_TIERS) - 1
        if lower > upper:
            raise ValueError("Minimum rank must not be higher than maximum rank")
        allowed = set(RANK_TIERS[lower : upper + 1])
        predicates.append(
            lambda account, tiers=allowed: str(
                _one(account, "rank.ranked_queues.tier") or "UNRANKED"
            ).upper() in tiers
        )

    for key, path, comparison in (
        ("level_min", "summoner.level", operator.ge),
        ("level_max", "summoner.level", operator.le),
        ("blue_essence_min", "loot.blue_essence", operator.ge),
        ("riot_points_min", "loot.riot_points", operator.ge),
    ):
        raw = str(filters.get(key) or "").strip()
        if raw:
            try:
                wanted = int(raw)
            except ValueError as exc:
                raise ValueError(f"{key.replace('_', ' ').title()} must be a number") from exc
            predicates.append(lambda account, p=path, op=comparison, w=wanted: op(int(_one(account, p) or 0), w))

    for key, path in (
        ("champions", "collection.champions.name"),
        ("skins", "collection.skins.name"),
        ("champion_shards", "loot.champion_shards.name"),
        ("skin_shards", "loot.skin_shards.name"),
    ):
        wanted = {item.strip().casefold() for item in str(filters.get(key) or "").split(",") if item.strip()}
        if wanted:
            predicates.append(lambda account, p=path, w=wanted: w <= {str(value).casefold() for value in _values(account, p)})
    return predicates


def _advanced_predicates(source: str) -> list:
    predicates = []
    for line_number, line in enumerate(source.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        match = EXPRESSION.match(line)
        if not match:
            raise ValueError(f"Invalid advanced filter on line {line_number}")
        field, symbol, raw = match.groups()
        path = FIELD_PATHS.get(field)
        if not path:
            raise ValueError(f"Unknown field on line {line_number}: {field}")
        predicates.append(lambda account, p=path, s=symbol, r=raw: any(_compare(value, s, r) for value in _values(account, p)))
    return predicates


def _values(value: Any, path: str) -> list[Any]:
    values = [value]
    for part in path.split("."):
        next_values = []
        for current in values:
            if isinstance(current, dict):
                child = current.get(part)
                next_values.extend(child if isinstance(child, list) else [child])
        values = next_values
    return [value for value in values if value is not None]


def _one(account: dict, path: str) -> Any:
    values = _values(account, path)
    return values[0] if values else None


def _compare(actual: Any, symbol: str, raw: str) -> bool:
    if symbol == "~":
        return raw.casefold() in str(actual).casefold()
    if isinstance(actual, bool):
        expected: Any = raw.casefold() in {"true", "yes", "1"}
    elif isinstance(actual, int):
        try:
            expected = int(raw)
        except ValueError:
            return False
    else:
        expected = raw
        if symbol in {"=", "!="}:
            actual, expected = str(actual).casefold(), expected.casefold()
    return {
        "=": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
    }[symbol](actual, expected)
