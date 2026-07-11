from __future__ import annotations

from enum import Enum


class Endpoint(str, Enum):
    CHAMPIONS = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json"
    SKINS = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/skins.json"
    CURRENCY = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/lolcurrency.json"
    INVENTORY_TYPE = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/lolinventorytype.json"
