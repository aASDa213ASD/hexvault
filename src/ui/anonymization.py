from __future__ import annotations

import hashlib
import random

from faker import Faker

_faker = Faker()
_FAKE_REGIONS = ("EUW", "RU", "EUNE", "NA", "KR")
_RANK_WEIGHTS = {
    "IRON": 0,
    "BRONZE": 0,
    "SILVER": 5,
    "GOLD": 10,
    "PLATINUM": 15,
    "EMERALD": 20,
    "DIAMOND": 50,
    "MASTER": 30,
    "GRANDMASTER": 25,
    "CHALLENGER": 1,
}
_RANK_TIERS = ("I", "II", "III", "IV")
_TIER_I_ONLY_RANKS = {"MASTER", "GRANDMASTER", "CHALLENGER"}


def _seed_for_summoner(summoner: dict) -> int:
    name = (summoner.get("name") or "").strip()
    tag = (summoner.get("tag") or "").strip()
    seed_source = f"{name}#{tag}"
    return int(hashlib.sha256(seed_source.encode("utf-8")).hexdigest(), 16) % (2**32)


def fake_username_for_summoner(summoner: dict) -> str:
    name = (summoner.get("name") or "").strip()
    tag = (summoner.get("tag") or "").strip()
    if not name and not tag:
        return "-"

    # Seed Faker per summoner identity so aliases stay stable across screens.
    _faker.seed_instance(_seed_for_summoner(summoner))
    fake_name = _faker.user_name()
    fake_tag = _faker.lexify(text="?????", letters="123456790").upper()
    return f"{fake_name}#{fake_tag}"


def fake_region_for_summoner(summoner: dict) -> str:
    name = (summoner.get("name") or "").strip()
    tag = (summoner.get("tag") or "").strip()
    if not name and not tag:
        return "-"
    seed = _seed_for_summoner(summoner)
    return _FAKE_REGIONS[seed % len(_FAKE_REGIONS)]


def fake_rank_for_account(account: dict, queue_key: str = "primary") -> tuple[str, str]:
    summoner = account.get("summoner") or {}
    account_id = str(account.get("id") or "")
    base_seed = _seed_for_summoner(summoner)
    queue_seed = int(
        hashlib.sha256(f"{account_id}:{queue_key}".encode("utf-8")).hexdigest(), 16
    ) % (2**32)
    rng = random.Random(base_seed ^ queue_seed)

    ranks = list(_RANK_WEIGHTS.keys())
    weights = list(_RANK_WEIGHTS.values())
    rank = rng.choices(ranks, weights=weights, k=1)[0]
    if rank in _TIER_I_ONLY_RANKS:
        return rank, "I"
    return rank, rng.choice(_RANK_TIERS)
