from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, TabPane


def compose_health_tab() -> ComposeResult:
    with TabPane("Health", id="health"):
        with VerticalScroll(id="health-tab", classes="section single-panel") as panel:
            panel.border_title = "Health"
            panel.border_subtitle = "Dependencies"
            with Horizontal(id="health-overview"):
                with Vertical(id="health-state-panel", classes="health-metric"):
                    yield Static("System status", classes="health-metric-label")
                    yield Static(
                        "Checking",
                        id="health-overall-state",
                        classes="health-metric-value",
                    )
                with Vertical(classes="health-metric"):
                    yield Static("Healthy", classes="health-metric-label")
                    yield Static("-", id="health-healthy-count", classes="health-metric-value")
                with Vertical(classes="health-metric"):
                    yield Static("Failing", classes="health-metric-label")
                    yield Static("-", id="health-failing-count", classes="health-metric-value")

            with Vertical(id="health-checks"):
                with Horizontal(id="health-check-db", classes="health-check") as row:
                    row.border_title = "Database"
                    with Vertical(classes="health-check-copy"):
                        yield Static("SQLite Storage", classes="health-check-title")
                        yield Static("-", id="health-detail-db", classes="health-check-detail")
                    yield Static("-", id="health-state-db", classes="health-check-state")
                with Horizontal(id="health-check-lcu", classes="health-check") as row:
                    row.border_title = "League Client"
                    with Vertical(classes="health-check-copy"):
                        yield Static("LCU Session", classes="health-check-title")
                        yield Static("-", id="health-detail-lcu", classes="health-check-detail")
                    yield Static("-", id="health-state-lcu", classes="health-check-state")
                with Horizontal(
                    id="health-check-community-dragon",
                    classes="health-check",
                ) as row:
                    row.border_title = "Community Dragon"
                    with Vertical(classes="health-check-copy"):
                        yield Static("Game assets and data", classes="health-check-title")
                        yield Static(
                            "-",
                            id="health-detail-community-dragon",
                            classes="health-check-detail",
                        )
                    yield Static(
                        "-",
                        id="health-state-community-dragon",
                        classes="health-check-state",
                    )
