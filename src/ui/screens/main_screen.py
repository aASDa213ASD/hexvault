from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, DataTable, Footer, Static, TabbedContent, TabPane

from src.database.connection import init_db
from src.lcu.client import get_current_summoner
from src.ui.anonymization import (
    fake_rank_for_account,
    fake_region_for_summoner,
    fake_username_for_summoner,
)
from src.ui.image_cache import prewarm_images
from src.ui.screens.account_credentials import AccountCredentialsScreen
from src.ui.screens.account_detail import AccountDetailScreen
from src.ui.widgets.remote_image import RemoteImage
from src.usecases.accounts import list_accounts
from src.usecases.health import health
from src.usecases.lcu import (
    current_account_exists,
    get_auto_accept_status,
    get_current_account_from_lcu,
    save_current_account,
)

ICON_SIZE = (16, 16)
RANK_ICON_SIZE = (16, 16)
RANKS_DIR = Path(__file__).resolve().parents[3] / "resources" / "ranks"


class Hexvault(App):
    BINDINGS = [("q", "quit", "Quit")]
    CSS = """
    .section-title {
        margin-bottom: 1;
        text-style: bold;
    }

    #accounts-layout {
        height: 1fr;
    }

    #accounts-table {
        width: 2fr;
    }

    #accounts-sidebar {
        width: 44;
        min-width: 44;
        padding-left: 3;
    }

    #details-hero {
        max-height: 10;
    }

    #summoner-title {
        text-style: bold;
    }

    #rank-row {
        height: auto;
    }

    #account-icon {
        width: 20;
        height: auto;
    }

    #rank-icon {
        width: 16;
        height: auto;
    }

    #rank-text {
        width: 1fr;
        padding-left: 1;
        content-align-vertical: middle;
        text-wrap: nowrap;
    }

    #account-summary {
        margin-top: 1;
    }

    """

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="accounts"):
            with TabPane("Accounts", id="accounts"):
                with Vertical():
                    yield Static(
                        "A depiction of all possessions one man could collect over the years",
                        classes="section-title",
                    )
                    with Horizontal(id="accounts-layout"):
                        yield DataTable(id="accounts-table")
                        with VerticalScroll(id="accounts-sidebar"):
                            yield Static("Account details", classes="section-title")
                            with Horizontal(id="details-hero"):
                                with Vertical(id="summoner-panel"):
                                    yield Static("-", id="summoner-title")
                                    yield RemoteImage(
                                        resize=ICON_SIZE,
                                        empty_text="No icon available",
                                        id="account-icon",
                                    )
                                with Vertical(id="rank-panel"):
                                    yield Static("-", id="rank-text")
                                    with Horizontal(id="rank-row"):
                                        yield RemoteImage(
                                            resize=RANK_ICON_SIZE,
                                            empty_text="",
                                            id="rank-icon",
                                        )
                            yield Static("No account selected", id="account-summary")
            with TabPane("LCU", id="lcu"):
                with Vertical():
                    yield Static("League Client API Handler", classes="section-title")
                    yield Static(id="lcu-status")
                    yield Button("Sync from client", id="lcu-sync", compact=True)
            with TabPane("Health", id="health"):
                with Vertical():
                    yield Static(
                        "Status page for overall application health and it's dependencies",
                        classes="section-title",
                    )
                    yield Static(id="health-status")
            with TabPane("Settings", id="settings"):
                with Vertical():
                    yield Static(
                        "Control how account details are displayed across the vault",
                        classes="section-title",
                    )
                    yield Checkbox("Hide names", id="setting-hide-names", compact=True)
                    yield Checkbox("Hide regions", id="setting-hide-regions", compact=True)
                    yield Checkbox(
                        "Randomize ranks",
                        id="setting-randomize-ranks",
                        compact=True,
                    )
        yield Footer()

    def on_mount(self) -> None:
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
            self.query_one("#account-summary", Static).update("No accounts found")
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
            rank_label = self._format_primary_rank_label(account)

            table.add_row(
                str(account.get("id", "")),
                self._format_summoner_name(summoner),
                self._format_region(summoner),
                str(summoner.get("level") or "-"),
                rank_label,
                str(loot.get("blue_essence") or "-"),
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

    def _format_primary_rank_label(self, account: dict) -> str:
        rank = account.get("rank") or {}
        ranked_queues = rank.get("ranked_queues") or []
        primary_queue = ranked_queues[0] if ranked_queues else {}
        if self._is_randomize_ranks_enabled():
            fake_rank, fake_tier = fake_rank_for_account(
                account,
                queue_key=str(primary_queue.get("type") or "primary"),
            )
            return f"{fake_rank} {fake_tier}"

        rank_label = primary_queue.get("tier") or "UNRANKED"
        division = primary_queue.get("division")
        if division:
            rank_label = f"{rank_label} {division}"
        return rank_label

    def _primary_rank_icon_tier(self, account: dict) -> str | None:
        rank = account.get("rank") or {}
        ranked_queues = rank.get("ranked_queues") or []
        primary_queue = ranked_queues[0] if ranked_queues else {}
        if self._is_randomize_ranks_enabled():
            fake_rank, _ = fake_rank_for_account(
                account,
                queue_key=str(primary_queue.get("type") or "primary"),
            )
            return fake_rank
        return primary_queue.get("tier")

    def _show_account_details(self, account: dict) -> None:
        summoner = account.get("summoner") or {}
        loot = account.get("loot") or {}
        collection = account.get("collection") or {}
        rank_label = self._format_primary_rank_label(account)

        self.query_one("#account-icon", RemoteImage).load_from_url(
            summoner.get("icon_url")
        )
        self.query_one("#summoner-title", Static).update(
            self._format_summoner_name(summoner)
        )
        self.query_one("#rank-icon", RemoteImage).load_from_path(
            self._get_rank_icon_path(self._primary_rank_icon_tier(account))
        )
        self.query_one("#rank-text", Static).update(rank_label)
        self.query_one("#account-summary", Static).update(
            "\n".join(
                [
                    f"Region: {self._format_region(summoner)}",
                    f"Level: {summoner.get('level') or '-'}",
                    f"Blue Essence: {loot.get('blue_essence') or '-'}",
                    f"RP: {loot.get('riot_points') or '-'}",
                    f"Champions: {len((collection.get('champions') or []))}",
                    f"Skins: {len((collection.get('skins') or []))}",
                ]
            )
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
            )
        )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id not in {
            "setting-hide-names",
            "setting-hide-regions",
            "setting-randomize-ranks",
        }:
            return
        selected_row = self.query_one("#accounts-table", DataTable).cursor_row
        self._populate_accounts_table()
        if 0 <= selected_row < len(self._accounts):
            self._show_account_details(self._accounts[selected_row])

    def _populate_lcu_status(self) -> None:
        # status = get_auto_accept_status()
        summoner = get_current_summoner()
        if not summoner:
            return
        
        lines = [
            f"Connected to {summoner.get('name')}#{summoner.get('tag')}"
        ]
        self.query_one("#lcu-status", Static).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
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
            sync_status = (
                f"sync: overwritten account '{name}'"
                if exists
                else f"sync: saved account '{name}'"
            )
            self._populate_accounts_table()
            self._populate_health_status()
            summoner = get_current_summoner()
            lines = [
                f"Connected to {summoner.get('name')}#{summoner.get('tag')}",
                sync_status
            ]
            self.query_one("#lcu-status", Static).update("\n".join(lines))
        except Exception as exc:
            summoner = get_current_summoner()
            lines = [
                f"Connected to {summoner.get('name')}#{summoner.get('tag')}",
                f"fatal: {exc}",
            ]
            self.query_one("#lcu-status", Static).update("\n".join(lines))

    def _save_new_account_with_credentials(
        self,
        current: dict,
        credentials: tuple[str, str] | None,
    ) -> None:
        summoner = current.get("summoner") or {}
        if credentials is None:
            lines = [
                f"Connected to {summoner.get('name')}#{summoner.get('tag')}",
                "sync: canceled",
            ]
            self.query_one("#lcu-status", Static).update("\n".join(lines))
            return

        login, password = credentials
        try:
            save_current_account(login=login, password=password, overwrite=False)
            name = self._format_summoner_name(summoner)
            sync_status = f"sync: saved account '{name}'"
            self._populate_accounts_table()
            self._populate_health_status()
            lines = [
                f"Connected to {summoner.get('name')}#{summoner.get('tag')}",
                sync_status,
            ]
            self.query_one("#lcu-status", Static).update("\n".join(lines))
        except Exception as exc:
            lines = [
                f"Connected to {summoner.get('name')}#{summoner.get('tag')}",
                f"fatal: {exc}",
            ]
            self.query_one("#lcu-status", Static).update("\n".join(lines))

    def _populate_health_status(self) -> None:
        status = health()
        lines = []
        for name, result in status.items():
            ok = result.get("ok")
            error = result.get("error")
            line = f"{name.upper()}: {'OPERATIONAL' if ok else 'FATAL'}"
            if error:
                line = f"{line} ({error})"
            lines.append(line)
        self.query_one("#health-status", Static).update("\n".join(lines))
