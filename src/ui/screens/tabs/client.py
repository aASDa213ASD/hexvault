from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, TabPane


def compose_client_tab() -> ComposeResult:
    with TabPane("Client", id="lcu"):
        with Vertical(id="posting-tab", classes="section single-panel") as panel:
            panel.border_title = "League Client"
            panel.border_subtitle = "LCU API Interface"
            with Horizontal(id="posting-actions"):
                yield Button(
                    "API Client",
                    id="open-posting-here",
                    classes="posting-action",
                )

