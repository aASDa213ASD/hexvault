from __future__ import annotations

import random

from src.datadragon.client import get_rank_icon_url, get_skins_map
from src.usecases.errors import ValidationError

RANK_TIERS = (
    "UNRANKED",
    "IRON",
    "BRONZE",
    "SILVER",
    "GOLD",
    "PLATINUM",
    "EMERALD",
    "DIAMOND",
    "MASTER",
    "GRANDMASTER",
    "CHALLENGER",
)

DEFAULT_RANK_WEIGHTS = {
    "UNRANKED": 25.0,
    "IRON": 1.0,
    "BRONZE": 1.0,
    "SILVER": 25.0,
    "GOLD": 25.0,
    "PLATINUM": 50.0,
    "EMERALD": 0.0,
    "DIAMOND": 50.0,
    "MASTER": 10.0,
    "GRANDMASTER": 0.0,
    "CHALLENGER": 0.0,
}


def _normalize_tier(value: str) -> str:
    return value.strip().upper()


def get_skins() -> dict:
    return get_skins_map()


def get_random_rank_icon(
    min_tier: str = "UNRANKED",
    max_tier: str = "CHALLENGER",
) -> dict:
    normalized_min = _normalize_tier(min_tier)
    normalized_max = _normalize_tier(max_tier)

    if normalized_min not in RANK_TIERS:
        raise ValidationError(f"Unknown min_tier: {min_tier}")
    
    if normalized_max not in RANK_TIERS:
        raise ValidationError(f"Unknown max_tier: {max_tier}")

    min_index = RANK_TIERS.index(normalized_min)
    max_index = RANK_TIERS.index(normalized_max)
    if min_index > max_index:
        raise ValidationError("min_tier must be lower or equal than max_tier")

    available_tiers = RANK_TIERS[min_index : max_index + 1]
    weighted_tiers = []
    weighted_values = []
    for tier in available_tiers:
        weighted_tiers.append(tier)
        weighted_values.append(DEFAULT_RANK_WEIGHTS.get(tier, 1.0))

    if not any(value > 0 for value in weighted_values):
        raise ValidationError("At least one tier in range must have weight > 0")

    selected_tier = random.choices(weighted_tiers, weights=weighted_values, k=1)[0]
    return {
        "tier": selected_tier,
        "icon_url": get_rank_icon_url(selected_tier.lower()),
    }
