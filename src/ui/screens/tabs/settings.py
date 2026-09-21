from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Checkbox, Select, Static, TabPane


def compose_settings_tab(theme_name: str) -> ComposeResult:
    with TabPane("Settings", id="settings"):
        with Vertical(classes="section single-panel") as panel:
            panel.border_title = "Preferences"
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
                with Horizontal(classes="setting-row") as row:
                    row.border_title = "Appearance"
                    with Vertical(classes="setting-copy"):
                        yield Static("Theme", classes="setting-title")
                        yield Static(
                            "Apply the same theme to Hexvault and Posting",
                            classes="setting-description",
                        )
                    yield Select(
                        (
                            ("Monochrome", "monochrome"),
                            ("CS 1.6", "cs16"),
                            ("Rose", "rose"),
                            ("Zen", "zen"),
                        ),
                        value=theme_name,
                        allow_blank=False,
                        id="setting-theme",
                        classes="setting-select",
                    )
