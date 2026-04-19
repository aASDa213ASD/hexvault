from __future__ import annotations

from enum import Enum


class Endpoint(str, Enum):
    CURRENT_SUMMONER = "/lol-summoner/v1/current-summoner"
    CURRENT_SUMMONER_ICON = "/lol-summoner/v1/current-summoner/icon"
    CURRENT_REGION = "/riotclient/region-locale"
    CURRENT_RANK = "/lol-ranked/v1/current-ranked-stats"
    CHALLENGES_PLAYER_PREFERENCES = "/lol-challenges/v1/update-player-preferences/"
    CURRENT_WALLET = "/lol-inventory/v1/wallet/rp"
    EMAIL_VERIFICATION = "/lol-email-verification/v1/email"
    OWNED_CHAMPIONS = "/lol-champions/v1/owned-champions-minimal"
    OWNED_SKINS = "/lol-inventory/v2/inventory/CHAMPION_SKIN"
    OWNED_LOOT = "/lol-loot/v1/player-loot"
    MATCHMAKING_SEARCH_STATE = "/lol-lobby/v2/lobby/matchmaking/search-state"
    READY_CHECK_ACCEPT = "/lol-matchmaking/v1/ready-check/accept"
    DODGE_CHAMP_SELECT = (
        "/lol-login/v1/session/invoke"
        '?destination=lcdsServiceProxy&method=call&args=["","teambuilder-draft","quitV2",""]'
    )
