from __future__ import annotations

from textual.theme import Theme


ICON_SIZE = (16, 16)
CLIENT_ICON_SIZE = (8, 8)
RANK_ICON_SIZE = (16, 16)
RANK_COLORS = {
    "Unranked": "#999999",
    "Iron": "#645E5A",
    "Bronze": "#8F745F",
    "Silver": "#CAD5E5",
    "Gold": "#FFD255",
    "Platinum": "#7FE4E1",
    "Emerald": "#24CA64",
    "Diamond": "#7497FF",
    "Master": "#F2A6FF",
    "Grandmaster": "#FF466B",
    "Challenger": "#FFE39D",
    "BE": "#B2DCFF",
}

HEXVAULT_THEME = Theme(
    name="hexvault",
    primary="#F4F1EA",
    secondary="#89B4FA",
    accent="#E6C384",
    foreground="#D7D3C8",
    background="#101014",
    surface="#181820",
    panel="#22222C",
    success="#A6D189",
    warning="#E6C384",
    error="#E78284",
    dark=True,
    variables={
        "block-cursor-text-style": "bold",
        "footer-key-foreground": "#89B4FA",
        "footer-key-background": "#181820",
        "footer-description-foreground": "#9A968E",
        "input-selection-background": "#89B4FA 28%",
    },
)

HEXVAULT_CSS = """
Hexvault {
    background: $background;
}

#app-root {
    padding: 1 1;
}

.section {
    border: round $accent 40%;
    border-title-align: right;
    border-title-color: $text-accent 50%;
    padding: 1 2;
}

.section:focus-within {
    border: round $accent 100%;
    border-title-color: $foreground;
    border-title-style: bold;
}

.muted {
    color: $text-muted;
}

#accounts-layout {
    height: 1fr;
}

#accounts-list-panel {
    width: 2fr;
    height: 1fr;
}

#accounts-table {
    width: 1fr;
    height: 1fr;
}

#accounts-sidebar {
    width: 48;
    min-width: 48;
    height: 1fr;
    margin-left: 1;
}

#selected-account-panel {
    width: 1fr;
    height: 1fr;
}

#details-hero {
    height: 10;
    max-height: 10;
}

#summoner-panel {
    width: 20;
    height: 10;
    border: round $surface-lighten-2;
    border-title-align: right;
    border-title-color: $text-muted;
    padding: 0 1;
    align-horizontal: center;
}

#summoner-title {
    display: none;
}

#rank-panel {
    width: 1fr;
    height: 10;
    border: round $surface-lighten-2;
    border-title-align: right;
    border-title-color: $text-muted;
    padding: 0 2;
    align-horizontal: center;
    align-vertical: middle;
}

#account-icon {
    width: 16;
    height: auto;
}

#rank-icon {
    width: 16;
    height: auto;
}

#account-summary {
    margin-top: 0;
    height: auto;
}

.summary-block {
    width: 1fr;
    height: 3;
    margin-bottom: 1;
    padding: 0 1;
    border: round $surface-lighten-1;
    border-title-align: right;
    border-title-color: $text-muted;
}

.summary-item {
    width: 1fr;
    height: 1;
}

.summary-item.right {
    align-horizontal: right;
}

.summary-label {
    width: auto;
    margin-right: 1;
    color: $text-muted;
    text-wrap: nowrap;
}

.summary-value {
    width: auto;
    color: $primary;
    text-style: bold;
    text-wrap: nowrap;
}

#connected-client {
    width: 1fr;
    height: 18;
    padding: 1 2;
}

#client-hero {
    width: 1fr;
    height: 10;
    margin-bottom: 1;
}

#client-icon-panel {
    width: 20;
    height: 10;
    border: round $surface-lighten-2;
    border-title-align: right;
    border-title-color: $text-muted;
    padding: 0 1;
    align-horizontal: center;
}

#client-icon {
    width: 16;
    height: auto;
}

#client-text-panel {
    width: 1fr;
    height: 10;
    border: round $surface-lighten-2;
    border-title-align: center;
    border-title-color: $text-muted;
    padding: 1 2;
}

.client-status {
    width: 1fr;
    height: 2;
    color: $primary;
    text-style: bold;
    text-wrap: wrap;
}

.client-sync-status {
    width: 1fr;
    height: 2;
    margin-top: 1;
    color: $text-muted;
    text-style: dim;
    text-wrap: wrap;
}

.single-panel {
    height: 1fr;
}

#lcu-actions {
    width: 1fr;
    height: auto;
}

.client-sync-button {
    width: 1fr;
}

#settings-options {
    height: auto;
}

.setting-row {
    width: 1fr;
    height: 5;
    margin-bottom: 1;
    padding: 0 1;
    border: round $surface-lighten-1;
    border-title-align: right;
    border-title-color: $text-muted;
}

.setting-copy {
    width: 1fr;
    height: auto;
}

.setting-title {
    text-style: bold;
    color: $foreground;
}

.setting-description {
    color: $text-muted;
    text-wrap: nowrap;
}

.setting-toggle {
    width: 5;
    height: 1;
    margin-top: 1;
    margin-left: 1;
}
"""
