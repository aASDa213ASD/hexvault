from __future__ import annotations

from textual.theme import Theme


ICON_SIZE = (16, 16)
CLIENT_ICON_SIZE = (8, 8)
RANK_ICON_SIZE = (16, 16)
MONOCHROME_THEME_COLORS = {
    "primary": "#F5F5F5",
    "secondary": "#A3A3A3",
    "accent": "#D4D4D4",
    "foreground": "#E5E5E5",
    "background": "#090909",
    "surface": "#141414",
    "panel": "#202020",
    "success": "#B5D6A7",
    "warning": "#D6C68A",
    "error": "#D98B8B",
}
CS16_THEME_COLORS = {
    "primary": "#C4B550",
    "secondary": "#8F8B72",
    "accent": "#D6CFAF",
    "foreground": "#DEDFD6",
    "background": "#171914",
    "surface": "#20231B",
    "panel": "#3E4637",
    "success": "#A0AA95",
    "warning": "#C4B550",
    "error": "#B85C4A",
}
ROSE_THEME_COLORS = {
    "primary": "#FF6B6B",
    "secondary": "#D94C5A",
    "accent": "#FCA5A5",
    "foreground": "#F3E8E8",
    "background": "#070506",
    "surface": "#100A0C",
    "panel": "#190F13",
    "success": "#86EFAC",
    "warning": "#FBBF24",
    "error": "#F43F5E",
}
ZEN_THEME_COLORS = {
    "primary": "#D7C9A9",
    "secondary": "#7E9482",
    "accent": "#B88A5A",
    "foreground": "#DDD8CA",

    "background": "#0B0B0A",
    "surface": "#131311",
    "panel": "#1C1C18",

    "success": "#819A78",
    "warning": "#C29B5B",
    "error": "#A95F58",
}
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

THEME_COLORS = {
    "monochrome": MONOCHROME_THEME_COLORS,
    "cs16": CS16_THEME_COLORS,
    "rose": ROSE_THEME_COLORS,
    "zen": ZEN_THEME_COLORS,
}
DEFAULT_THEME_NAME = "monochrome"


def _make_theme(name: str, colors: dict[str, str]) -> Theme:
    return Theme(
        name=name,
        primary=colors["primary"],
        secondary=colors["secondary"],
        accent=colors["accent"],
        foreground=colors["foreground"],
        background=colors["background"],
        surface=colors["surface"],
        panel=colors["panel"],
        success=colors["success"],
        warning=colors["warning"],
        error=colors["error"],
        dark=True,
        variables={
            "block-cursor-text-style": "bold",
            "footer-key-foreground": colors["primary"],
            "footer-key-background": colors["surface"],
            "footer-description-foreground": colors["secondary"],
            "input-selection-background": f'{colors["primary"]} 28%',
        },
    )


THEMES = {
    name: _make_theme(name, colors)
    for name, colors in THEME_COLORS.items()
}

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
    padding: 0 1;
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

#posting-tab {
    padding: 1 2;
}

#posting-actions {
    height: auto;
}

.posting-action {
    width: 1fr;
    margin-right: 1;
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

.setting-select {
    width: 20;
    margin-left: 1;
}

#health-tab {
    padding: 1 2;
}

#search-layout {
    height: 1fr;
}

#search-filters {
    width: 3fr;
    min-width: 58;
    margin-right: 1;
}

#search-results-panel {
    width: 4fr;
    height: 1fr;
}

#search-results {
    height: 1fr;
}

.search-heading {
    margin-top: 1;
    color: $foreground;
    text-style: bold;
}

.search-copy {
    padding-left: 1;
}

.search-row {
    height: 3;
}

.search-row Input {
    width: 1fr;
}

.search-row Select {
    width: 1fr;
}

#search-advanced {
    height: 6;
}

#search-actions {
    height: 3;
    margin-top: 1;
}

#search-actions Button {
    width: 1fr;
}

#health-overview {
    width: 1fr;
    height: auto;
}

.health-metric {
    width: 1fr;
    height: 6;
    margin-right: 1;
    padding: 0 1;
    border: round $surface-lighten-1;
    border-title-align: right;
    align-horizontal: center;
    align-vertical: middle;
}

.health-metric-value {
    width: 1fr;
    height: 1;
    color: $primary;
    text-style: bold;
    text-align: center;
}

.health-metric-label {
    width: 1fr;
    height: 1;
    color: $text-muted;
    text-align: center;
}

#health-checks {
    width: 1fr;
    height: auto;
    padding-top: 1;
}

.health-check {
    width: 1fr;
    height: 5;
    margin-bottom: 1;
    padding: 0 1;
    border: round $surface-lighten-1;
    border-title-align: right;
    border-title-color: $text-muted;
}

.health-check.ok {
    border: round $success 60%;
}

.health-check.fatal {
    border: round $error 70%;
}

.health-check-copy {
    width: 1fr;
    height: auto;
    border-title-align: right;
    border-title-color: $text-muted;
}

.health-check-title {
    color: $foreground;
    text-style: bold;
}

.health-check-detail {
    color: $text-muted;
    text-wrap: wrap;
}

.health-check-state {
    width: 10;
    height: 1;
    margin-top: 1;
    margin-left: 1;
    text-align: right;
    text-style: bold;
}

.health-check-state.ok {
    color: $success;
}

.health-check-state.fatal {
    color: $error;
}
"""
