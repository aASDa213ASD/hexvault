from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, DataTable, Footer, Static, TabbedContent, TabPane

from src.database.connection import init_db
from src.lcu.client import get_current_summoner
from intergration.posting.posting import (
    prepare_lcu_posting_workspace,
    run_lcu_posting_foreground,
)
from src.ui.anonymization import (
    fake_rank_for_account,
    fake_region_for_summoner,
    fake_username_for_summoner,
)
from src.ui.image_cache import prewarm_images
from src.ui.screens.account_credentials import AccountCredentialsScreen
from src.ui.screens.account_detail import AccountDetailScreen
from src.ui.theme import (
    HEXVAULT_CSS,
    HEXVAULT_THEME,
    ICON_SIZE,
    RANK_COLORS,
    RANK_ICON_SIZE,
)
from src.ui.widgets.remote_image import RemoteImage
from src.usecases.accounts import list_accounts
from src.usecases.health import health
from src.usecases.lcu import (
    current_account_exists,
    get_auto_accept_status,
    get_current_account_from_lcu,
    save_current_account,
)


RANKS_DIR = Path(__file__).resolve().parents[3] / "resources" / "ranks"


class Hexvault(App):
    BINDINGS = [("q", "quit", "Quit")]
    CSS = HEXVAULT_CSS

    def __init__(self) -> None:
        self._posting_workspace = prepare_lcu_posting_workspace()
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="app-root"):
            with TabbedContent(initial="accounts"):
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
                                    with Vertical(id="client-icon-panel") as panel:
                                        yield RemoteImage(
                                            resize=ICON_SIZE,
                                            empty_text="No icon",
                                            id="client-icon",
                                        )
                                    with Vertical(id="client-text-panel") as panel:
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
                
                with TabPane("Client", id="lcu"):
                    with Vertical(id="posting-tab", classes="section single-panel") as panel:
                        panel.border_title = "League Client"
                        panel.border_subtitle = "LCU API Interface"
                        yield Static(
                            self._posting_workspace.status,
                            id="posting-status",
                            classes="posting-status",
                        )
                        with Horizontal(id="posting-actions"):
                            yield Button(
                                "API Client",
                                id="open-posting-here",
                                classes="posting-action",
                            )
                
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
                
                with TabPane("Health", id="health"):
                    with Vertical(classes="section single-panel") as panel:
                        panel.border_title = "Health"
                        panel.border_subtitle = "Dependencies"
                        yield Static(id="health-status", classes="status-copy")
        
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(HEXVAULT_THEME)
        self.theme = "hexvault"
        init_db()
        self._accounts: list[dict] = []
        self._populate_accounts_table()
        self._populate_lcu_status()
        self._populate_health_status()

    def _populate_accounts_table(self) -> None:
        table = self.query_one("#accounts-table", DataTable)
        table.clear(columns=True)
        table.cursor_type = "row"
        table.add_columns("ID", "Summoner", "Region", "Level", "Rank", "Blue Essence")

        self._accounts = list_accounts()
        if not self._accounts:
            self.query_one("#account-icon", RemoteImage).load_from_url(None)
            self.query_one("#account-region", Static).update("-")
            self.query_one("#account-level", Static).update("-")
            self.query_one("#blue-essence", Static).update("-")
            self.query_one("#riot-points", Static).update("-")
            self.query_one("#champions-count", Static).update("-")
            self.query_one("#skins-count", Static).update("-")
            table.add_row("-", "No accounts found", "-", "-", "-", "-")
            return

        prewarm_images(
            [
                summoner.get("icon_url")
                for account in self._accounts
                for summoner in [account.get("summoner") or {}]
                if summoner.get("icon_url")
            ],
            resize=ICON_SIZE,
        )

        for account in self._accounts:
            summoner = account.get("summoner") or {}
            loot = account.get("loot") or {}
            ranked_queues = (account.get("rank") or {}).get("ranked_queues") or []
            primary_queue = ranked_queues[0] if ranked_queues else {}
            if self._is_randomize_ranks_enabled():
                fake_rank, fake_tier = fake_rank_for_account(
                    account,
                    queue_key=str(primary_queue.get("type") or "primary"),
                )
                rank_label = f"{fake_rank} {fake_tier}"
                rank_tier = fake_rank
            else:
                rank_tier = primary_queue.get("tier") or "Unranked"
                rank_label = rank_tier
                division = primary_queue.get("division")
                if division:
                    rank_label = f"{rank_label} {division}"

            table.add_row(
                Text(str(account.get("id", "")), style="dim"),
                Text(self._format_summoner_name(summoner), style="$primary"),
                Text(self._format_region(summoner), style="dim"),
                Text(str(summoner.get("level") or "-"), style="dim"),
                Text(rank_label, style=RANK_COLORS.get(rank_tier, "")),
                Text(str(loot.get("blue_essence") or "-"), style="#B2DCFF"),
            )

        self._show_account_details(self._accounts[0])

    def _format_summoner_name(self, summoner: dict) -> str:
        if self._is_hide_names_enabled():
            return fake_username_for_summoner(summoner)
        
        name = summoner.get("name")
        tag = summoner.get("tag")
        if name and tag:
            return f"{name}#{tag}"
        
        return name or "-"

    def _is_hide_names_enabled(self) -> bool:
        return self.query_one("#setting-hide-names", Checkbox).value

    def _is_hide_regions_enabled(self) -> bool:
        return self.query_one("#setting-hide-regions", Checkbox).value

    def _is_randomize_ranks_enabled(self) -> bool:
        return self.query_one("#setting-randomize-ranks", Checkbox).value

    def _format_region(self, summoner: dict) -> str:
        if self._is_hide_regions_enabled():
            return fake_region_for_summoner(summoner)
        return summoner.get("region") or "-"

    def _show_account_details(self, account: dict) -> None:
        summoner = account.get("summoner") or {}
        loot = account.get("loot") or {}
        collection = account.get("collection") or {}
        ranked_queues = (account.get("rank") or {}).get("ranked_queues") or []
        primary_queue = ranked_queues[0] if ranked_queues else {}
        rank_icon_tier = primary_queue.get("tier")
        if self._is_randomize_ranks_enabled():
            fake_rank, fake_tier = fake_rank_for_account(
                account,
                queue_key=str(primary_queue.get("type") or "primary"),
            )
            rank_label = f"{fake_rank} {fake_tier}"
            rank_icon_tier = fake_rank
        else:
            rank_label = primary_queue.get("tier") or "UNRANKED"
            division = primary_queue.get("division")
            if division:
                rank_label = f"{rank_label} {division}"

        self.query_one("#account-icon", RemoteImage).load_from_url(
            summoner.get("icon_url")
        )
        self.query_one("#summoner-panel", Vertical).border_title = (
            self._format_summoner_name(summoner)
        )
        self.query_one("#rank-icon", RemoteImage).load_from_path(
            self._get_rank_icon_path(rank_icon_tier)
        )
        self.query_one("#rank-panel", Vertical).border_title = rank_label
        self.query_one("#account-region", Static).update(self._format_region(summoner))
        self.query_one("#account-level", Static).update(str(summoner.get("level") or "0"))
        self.query_one("#blue-essence", Static).update(str(loot.get("blue_essence") or "0"))
        self.query_one("#riot-points", Static).update(str(loot.get("riot_points") or "0"))
        self.query_one("#champions-count", Static).update(
            str(len((collection.get("champions") or [])))
        )
        self.query_one("#skins-count", Static).update(
            str(len((collection.get("skins") or [])))
        )

    def _get_rank_icon_path(self, tier: str | None) -> Path | None:
        rank_name = (tier or "UNRANKED").strip().lower()
        rank_path = RANKS_DIR / f"{rank_name}.png"
        if rank_path.exists():
            return rank_path
        
        fallback_path = RANKS_DIR / "unranked.png"
        return fallback_path if fallback_path.exists() else None

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.cursor_row < 0 or event.cursor_row >= len(self._accounts):
            return
        
        self._show_account_details(self._accounts[event.cursor_row])

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.cursor_row < 0 or event.cursor_row >= len(self._accounts):
            return
        
        self.push_screen(
            AccountDetailScreen(
                self._accounts[event.cursor_row],
                hide_names=self._is_hide_names_enabled(),
                hide_regions=self._is_hide_regions_enabled(),
                randomize_ranks=self._is_randomize_ranks_enabled(),
            ),
            callback=self._on_account_detail_closed,
        )

    def _on_account_detail_closed(self, was_deleted: bool | None) -> None:
        if was_deleted:
            self._populate_accounts_table()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id not in {
            "setting-hide-names",
            "setting-hide-regions",
            "setting-randomize-ranks",
        }: return

        selected_row = self.query_one("#accounts-table", DataTable).cursor_row
        self._populate_accounts_table()
        if 0 <= selected_row < len(self._accounts):
            self._show_account_details(self._accounts[selected_row])

    def _populate_lcu_status(self) -> None:
        # status = get_auto_accept_status()
        summoner = get_current_summoner()
        if not summoner:
            self.query_one("#client-icon", RemoteImage).load_from_url(None)
            self.query_one("#lcu-status", Static).update("Not connected")
            self.query_one("#lcu-sync-status", Static).update("")
            return

        self.query_one("#client-icon", RemoteImage).load_from_url(
            summoner.get("icon_url")
        )
        self._set_lcu_welcome(summoner)

    def _set_lcu_welcome(self, summoner: dict | None) -> None:
        if not summoner:
            self.query_one("#lcu-status", Static).update("Not connected")
            return
        
        self.query_one("#lcu-status", Static).update(
            f"Welcome back, {summoner.get('name')}#{summoner.get('tag')}"
        )

    def _set_lcu_sync_status(self, message: str) -> None:
        self.query_one("#lcu-sync-status", Static).update(message)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "open-posting-here":
            with self.suspend():
                status = run_lcu_posting_foreground()
            return

        if event.button.id != "lcu-sync":
            return
        
        self._sync_current_account()

    def _sync_current_account(self) -> None:
        try:
            current = get_current_account_from_lcu()
            exists = current_account_exists().get("exists", False)
            if not exists:
                self.push_screen(
                    AccountCredentialsScreen(),
                    callback=lambda credentials: self._save_new_account_with_credentials(
                        current, credentials
                    ),
                )
                return

            save_current_account(overwrite=True)
            summoner = current.get("summoner") or {}
            name = self._format_summoner_name(summoner)
            sync_status = f"Account synced - {name}"
            self._populate_accounts_table()
            self._populate_health_status()
            summoner = get_current_summoner()
            self.query_one("#client-icon", RemoteImage).load_from_url(
                summoner.get("icon_url") if summoner else None
            )
            self._set_lcu_welcome(summoner)
            self._set_lcu_sync_status(sync_status)
        except Exception as exc:
            summoner = get_current_summoner()
            self.query_one("#client-icon", RemoteImage).load_from_url(
                summoner.get("icon_url") if summoner else None
            )
            self._set_lcu_welcome(summoner)
            self._set_lcu_sync_status(f"fatal: {exc}")

    def _save_new_account_with_credentials(
        self,
        current: dict,
        credentials: tuple[str, str] | None,
    ) -> None:
        summoner = current.get("summoner") or {}
        if credentials is None:
            self.query_one("#client-icon", RemoteImage).load_from_url(
                summoner.get("icon_url")
            )
            self._set_lcu_welcome(summoner)
            self._set_lcu_sync_status("Sync has been cancelled")
            return

        login, password = credentials
        try:
            save_current_account(login=login, password=password, overwrite=False)
            name = self._format_summoner_name(summoner)
            sync_status = f"Account added {name}"
            self._populate_accounts_table()
            self._populate_health_status()
            self.query_one("#client-icon", RemoteImage).load_from_url(
                summoner.get("icon_url")
            )
            self._set_lcu_welcome(summoner)
            self._set_lcu_sync_status(sync_status)
        except Exception as exc:
            self.query_one("#client-icon", RemoteImage).load_from_url(
                summoner.get("icon_url")
            )
            self._set_lcu_welcome(summoner)
            self._set_lcu_sync_status(f"fatal: {exc}")

    def _populate_health_status(self) -> None:
        status = health()
        lines = []
        for name, result in status.items():
            ok = result.get("ok")
            error = result.get("error")
            line = f"{name}: {'Operational' if ok else 'Fatal'}"
            if error:
                line = f"{line} ({error})"
            lines.append(line)
        self.query_one("#health-status", Static).update("\n".join(lines))
