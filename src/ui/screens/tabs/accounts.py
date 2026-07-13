from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, DataTable, Static, TabPane

from src.ui.shared.theme import ICON_SIZE, RANK_ICON_SIZE
from src.ui.widgets.remote_image import RemoteImage


def compose_accounts_tab() -> ComposeResult:
    with TabPane("Accounts", id="accounts"):
        with Horizontal(id="accounts-layout"):
            with Vertical(id="accounts-list-panel", classes="section") as panel:
                panel.border_title = "Vault"
                panel.border_subtitle = "Enter to open the account"
                yield DataTable(id="accounts-table")

            with Vertical(id="accounts-sidebar"):
                with VerticalScroll(id="selected-account-panel", classes="section") as panel:
                    panel.border_title = "Selected account"
                    panel.border_subtitle = "Live preview"
                    with Horizontal(id="details-hero"):
                        with Vertical(id="summoner-panel") as panel:
                            panel.border_title = "-"
                            yield RemoteImage(
                                resize=ICON_SIZE,
                                empty_text="No icon available",
                                id="account-icon",
                            )
                        with Vertical(id="rank-panel") as panel:
                            panel.border_title = "-"
                            with Horizontal(id="rank-row"):
                                yield RemoteImage(
                                    resize=RANK_ICON_SIZE,
                                    empty_text="",
                                    id="rank-icon",
                                )
                    with Vertical(id="account-summary"):
                        with Horizontal(
                            classes="summary-block",
                            id="account-meta",
                        ) as account_meta:
                            account_meta.border_title = "Account"
                            with Horizontal(classes="summary-item"):
                                yield Static("Region", classes="summary-label")
                                yield Static("-", classes="summary-value", id="account-region")
                            with Horizontal(classes="summary-item right"):
                                yield Static("Level", classes="summary-label")
                                yield Static("-", classes="summary-value", id="account-level")
                        with Horizontal(
                            classes="summary-block",
                            id="currency-meta",
                        ) as currency_meta:
                            currency_meta.border_title = "Currency"
                            with Horizontal(classes="summary-item"):
                                yield Static("Blue Essence", classes="summary-label")
                                yield Static("-", classes="summary-value", id="blue-essence")
                            with Horizontal(classes="summary-item right"):
                                yield Static("Riot Points", classes="summary-label")
                                yield Static("-", classes="summary-value", id="riot-points")
                        with Horizontal(
                            classes="summary-block",
                            id="collection-meta",
                        ) as collection_meta:
                            collection_meta.border_title = "Collection"
                            with Horizontal(classes="summary-item"):
                                yield Static("Champions", classes="summary-label")
                                yield Static("-", classes="summary-value", id="champions-count")
                            with Horizontal(classes="summary-item right"):
                                yield Static("Skins", classes="summary-label")
                                yield Static("-", classes="summary-value", id="skins-count")

                with Vertical(id="connected-client", classes="section") as panel:
                    panel.border_title = "Connected client"
                    with Horizontal(id="client-hero"):
                        with Vertical(id="client-icon-panel"):
                            yield RemoteImage(
                                resize=ICON_SIZE,
                                empty_text="No icon",
                                id="client-icon",
                            )
                        with Vertical(id="client-text-panel"):
                            yield Static(
                                "Not connected",
                                id="lcu-status",
                                classes="client-status",
                            )
                            yield Static(
                                "",
                                id="lcu-sync-status",
                                classes="client-sync-status",
                            )

                    with Horizontal(id="lcu-actions"):
                        yield Button(
                            "Sync",
                            id="lcu-sync",
                            classes="client-sync-button",
                        )

