from __future__ import annotations

from enum import Enum


class Endpoint(str, Enum):
    SKINS = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/skins.json"
