from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, DataTable, Input, Select, Static, TabPane, TextArea

from src.usecases.datadragon import RANK_TIERS


def compose_search_tab() -> ComposeResult:
    with TabPane("Search", id="search"):
        with Horizontal(id="search-layout"):
            with VerticalScroll(id="search-filters", classes="section") as panel:
                panel.border_title = "Search parameters"
                yield Static("Region and level", classes="search-heading search-copy")
                with Horizontal(classes="search-row"):
                    yield Input(placeholder="Region (e.g. EUW)", id="search-region")
                    yield Input(placeholder="Level (min)", id="search-level-min", type="integer")
                    yield Input(placeholder="Level (max)", id="search-level-max", type="integer")
                yield Static("Rank range", classes="search-heading search-copy")
                with Horizontal(classes="search-row"):
                    yield Select(
                        [(tier.title(), tier) for tier in RANK_TIERS],
                        prompt="Rank from",
                        id="search-rank-min",
                    )
                    yield Select(
                        [(tier.title(), tier) for tier in RANK_TIERS],
                        prompt="Rank to",
                        id="search-rank-max",
                    )
                yield Static("Owned collection (comma-separated; all are required)", classes="search-heading search-copy")
                yield Input(placeholder="Champions: Draven, Yasuo, Yone", id="search-champions")
                yield Input(placeholder="Skins: Gladiator Draven, Nightbringer Yasuo", id="search-skins")
                yield Static("Loot", classes="search-heading search-copy")
                with Horizontal(classes="search-row"):
                    yield Input(placeholder="Blue Essence (min)", id="search-be-min", type="integer")
                    yield Input(placeholder="Riot Points (min)", id="search-rp-min", type="integer")
                yield Input(placeholder="Champion shards (all required)", id="search-champion-shards")
                yield Input(placeholder="Skin shards (all required)", id="search-skin-shards")
                yield Static("Advanced filters — one per line: field operator value", classes="search-heading search-copy")
                yield Static("Operators: =  !=  ~ (contains)  >  >=  <  <=", classes="muted search-copy")
                yield Static("Examples: loot.keys >= 1 · ranked_queues.tier = GOLD · verification.email ~ gmail", classes="muted search-copy")
                yield TextArea("", id="search-advanced")
                with Horizontal(id="search-actions"):
                    yield Button("Search", id="search-submit")
                    yield Button("Clear", id="search-clear")
                yield Static("", id="search-status", classes="muted")
            with Vertical(id="search-results-panel", classes="section") as panel:
                panel.border_title = "Results"
                panel.border_subtitle = "Enter to open the account"
                yield DataTable(id="search-results")
