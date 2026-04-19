from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Checkbox, DataTable, Footer, Static, TabbedContent, TabPane

from src.database.connection import init_db
from src.ui.image_cache import prewarm_images
from src.ui.screens.account_detail import AccountDetailScreen
from src.ui.widgets.remote_image import RemoteImage
from src.usecases.accounts import list_accounts
from src.usecases.health import health
from src.usecases.lcu import get_auto_accept_status

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
                    yield Static("LCU", classes="section-title")
                    yield Static(id="lcu-status")
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
                    yield Checkbox("Hide tags", id="setting-hide-tags", compact=True)
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
            rank = account.get("rank") or {}
            ranked_queues = rank.get("ranked_queues") or []

            primary_queue = ranked_queues[0] if ranked_queues else {}
            rank_label = primary_queue.get("tier") or "UNRANKED"
            division = primary_queue.get("division")
            if division:
                rank_label = f"{rank_label} {division}"

            table.add_row(
                str(account.get("id", "")),
                self._format_summoner_name(summoner),
                summoner.get("region") or "-",
                str(summoner.get("level") or "-"),
                rank_label,
                str(loot.get("blue_essence") or "-"),
            )

        self._show_account_details(self._accounts[0])

    def _format_summoner_name(self, summoner: dict) -> str:
        name = summoner.get("name")
        tag = summoner.get("tag")
        if name and tag:
            return f"{name}#{tag}"
        return name or "-"

    def _show_account_details(self, account: dict) -> None:
        summoner = account.get("summoner") or {}
        loot = account.get("loot") or {}
        collection = account.get("collection") or {}
        rank = account.get("rank") or {}
        ranked_queues = rank.get("ranked_queues") or []

        primary_queue = ranked_queues[0] if ranked_queues else {}
        rank_label = primary_queue.get("tier") or "UNRANKED"
        division = primary_queue.get("division")
        if division:
            rank_label = f"{rank_label} {division}"

        self.query_one("#account-icon", RemoteImage).load_from_url(
            summoner.get("icon_url")
        )
        self.query_one("#summoner-title", Static).update(
            self._format_summoner_name(summoner)
        )
        self.query_one("#rank-icon", RemoteImage).load_from_path(
            self._get_rank_icon_path(primary_queue.get("tier"))
        )
        self.query_one("#rank-text", Static).update(rank_label)
        self.query_one("#account-summary", Static).update(
            "\n".join(
                [
                    f"Region: {summoner.get('region') or '-'}",
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
        self.push_screen(AccountDetailScreen(self._accounts[event.cursor_row]))

    def _populate_lcu_status(self) -> None:
        status = get_auto_accept_status()
        lines = [
            f"running: {status.get('running')}",
            f"last_state: {status.get('last_state') or '-'}",
            f"accepted_count: {status.get('accepted_count')}",
            f"last_error: {status.get('last_error') or '-'}",
        ]
        self.query_one("#lcu-status", Static).update("\n".join(lines))

    def _populate_health_status(self) -> None:
        status = health()
        lines = []
        for name, result in status.items():
            ok = result.get("ok")
            error = result.get("error")
            line = f"{name}: {'ok' if ok else 'failed'}"
            if error:
                line = f"{line} ({error})"
            lines.append(line)
        self.query_one("#health-status", Static).update("\n".join(lines))
