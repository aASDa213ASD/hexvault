from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Checkbox, Static, TabPane


def compose_settings_tab() -> ComposeResult:
    with TabPane("Settings", id="settings"):
        with Vertical(classes="section single-panel") as panel:
            panel.border_title = "Privacy"
            panel.border_subtitle = "Display controls"
            with Vertical(id="settings-options"):
                with Horizontal(classes="setting-row") as row:
                    row.border_title = "Summoner names"
                    with Vertical(classes="setting-copy"):
                        yield Static("Hide names", classes="setting-title")
                        yield Static(
                            "Replace Riot IDs with fake generated names",
                            classes="setting-description",
                        )
                    yield Checkbox(
                        id="setting-hide-names",
                        compact=True,
                        classes="setting-toggle",
                    )
                with Horizontal(classes="setting-row") as row:
                    row.border_title = "Regions"
                    with Vertical(classes="setting-copy"):
                        yield Static("Hide regions", classes="setting-title")
                        yield Static(
                            "Show generated server codes instead of real regions",
                            classes="setting-description",
                        )
                    yield Checkbox(
                        id="setting-hide-regions",
                        compact=True,
                        classes="setting-toggle",
                    )
                with Horizontal(classes="setting-row") as row:
                    row.border_title = "Ranks"
                    with Vertical(classes="setting-copy"):
                        yield Static("Randomize ranks", classes="setting-title")
                        yield Static(
                            "Display deterministic fake ranks to hide the fact that you are low elo",
                            classes="setting-description",
                        )
                    yield Checkbox(
                        id="setting-randomize-ranks",
                        compact=True,
                        classes="setting-toggle",
                    )

