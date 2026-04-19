from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Static,
    TabbedContent,
    TabPane,
)

from src.database.connection import init_db
from src.ui.image_cache import prewarm_images
from src.ui.widgets.remote_image import RemoteImage
from src.usecases.accounts import list_accounts
from src.usecases.health import health
from src.usecases.lcu import get_auto_accept_status

ICON_SIZE = (16, 16)
RANK_ICON_SIZE = (16, 16)
RANKS_DIR = Path(__file__).resolve().parent / "resources" / "ranks"


class AccountDetailScreen(Screen[None]):
    BINDINGS = [("q", "close_screen", "Back")]
    CSS = """
    #detail-root {
        padding: 1 2;
    }

    #detail-hero {
        max-height: 10;
        margin-bottom: 1;
    }

    #detail-account-icon {
        width: 18;
        height: auto;
        margin-right: 2;
    }

    .muted {
        color: $text-muted;
    }

    .detail-table {
        min-height: 24;
        max-height: 44;
    }
    """

    def __init__(self, account: dict) -> None:
        super().__init__()
        self.account = account

    def compose(self) -> ComposeResult:
        summoner = self.account.get("summoner") or {}
        collection = self.account.get("collection") or {}
        loot = self.account.get("loot") or {}
        with VerticalScroll(id="detail-root"):
            with Horizontal(id="detail-hero"):
                yield RemoteImage(
                    summoner.get("icon_url"),
                    resize=ICON_SIZE,
                    empty_text="No icon available",
                    id="detail-account-icon",
                )
                with Vertical():
                    yield Static(self._format_summoner_name(summoner), id="detail-title")
                    yield Static(
                        f"{summoner.get('region') or '-'}  Level {summoner.get('level') or '-'}",
                        classes="muted",
                    )
                    yield Static(self._primary_rank_label())
                    yield Static(
                        "  ".join(
                            [
                                f"Champions {len(collection.get('champions') or [])}",
                                f"Skins {len(collection.get('skins') or [])}",
                                f"BE {loot.get('blue_essence') or 0}",
                                f"RP {loot.get('riot_points') or 0}",
                            ]
                        ),
                        classes="muted",
                    )
            with TabbedContent(initial="overview"):
                with TabPane("Overview", id="overview"):
                    yield Static(self._build_overview())
                with TabPane("Champions", id="champions"):
                    yield Input(
                        placeholder="Search champions...",
                        id="detail-champions-search",
                        compact=True
                    )
                    yield DataTable(id="detail-champions-table", classes="detail-table")
                with TabPane("Skins", id="skins"):
                    yield Input(
                        placeholder="Search skins...",
                        id="detail-skins-search",
                        compact=True
                    )
                    yield DataTable(id="detail-skins-table", classes="detail-table")
                with TabPane("Loot", id="loot"):
                    yield DataTable(id="detail-loot-table", classes="detail-table")
        yield Footer()

    def on_mount(self) -> None:
        self._populate_champions_table()
        self._populate_skins_table()
        self._populate_loot_table()

    def _build_overview(self) -> str:
        summoner = self.account.get("summoner") or {}
        verification = self.account.get("verification") or {}
        credentials = self.account.get("credentials") or {}
        collection = self.account.get("collection") or {}
        loot = self.account.get("loot") or {}
        champions = collection.get("champions") or []
        skins = collection.get("skins") or []

        lines = [
            f"Account ID: {self.account.get('id', '-')}",
            "",
            f"Region: {summoner.get('region') or '-'}",
            f"Level: {summoner.get('level') or '-'}",
            f"Email: {verification.get('email') or '-'}",
            f"Login: {credentials.get('login') or '-'}",
            "",
            "Currencies",
            f"- Blue Essence: {loot.get('blue_essence') or 0}",
            f"- Orange Essence: {loot.get('orange_essence') or 0}",
            f"- Riot Points: {loot.get('riot_points') or 0}",
            "",
            "Collection",
            f"- Champions: {len(champions)}",
            f"- Skins: {len(skins)}",
            "",
            "Ranked Queues",
        ]

        ranked_queues = self._ranked_queues()
        if ranked_queues:
            for queue in ranked_queues:
                tier = queue.get("tier") or "UNRANKED"
                division = queue.get("division")
                label = f"{tier} {division}" if division else tier
                lines.append(
                    f"- {queue.get('type') or '-'}: {label}, "
                    f"{queue.get('league_points', 0)} LP, "
                    f"{queue.get('wins', 0)}W/{queue.get('losses', 0)}L"
                )
        else:
            lines.append("- No ranked data")

        return "\n".join(lines)

    def _populate_champions_table(self) -> None:
        table = self.query_one("#detail-champions-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Champion ID", "Name", "Alias", "Title")
        champions = self._filtered_champions()
        if not champions:
            table.add_row("-", "No champions found", "-", "-")
            return
        for champion in champions:
            table.add_row(
                champion.get("champion_id") or "-",
                champion.get("name") or "-",
                champion.get("alias") or "-",
                champion.get("title") or "-",
            )

    def _populate_skins_table(self) -> None:
        table = self.query_one("#detail-skins-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Skin ID", "Name")
        skins = self._filtered_skins()
        if not skins:
            table.add_row("-", "No skins found")
            return
        for skin in skins:
            table.add_row(
                skin.get("skin_id") or "-",
                skin.get("name") or "-",
            )

    def _populate_loot_table(self) -> None:
        table = self.query_one("#detail-loot-table", DataTable)
        table.add_columns("Type", "Name", "Amount", "Disenchant")
        loot = self.account.get("loot") or {}
        champion_shards = loot.get("champion_shards") or []
        skin_shards = loot.get("skin_shards") or []
        entries = [("Champion", shard) for shard in champion_shards] + [
            ("Skin", shard) for shard in skin_shards
        ]
        if not entries:
            table.add_row("No loot", "-", "-", "-")
            return
        for entry_type, shard in entries:
            table.add_row(
                shard.get("type") or "-",
                shard.get("name") or "-",
                str(shard.get("amount") or 0),
                str(shard.get("disenchant_value") or 0),
            )

    def _ranked_queues(self) -> list[dict]:
        rank = self.account.get("rank") or {}
        return rank.get("ranked_queues") or []

    def _primary_rank_label(self) -> str:
        ranked_queues = self._ranked_queues()
        if not ranked_queues:
            return "UNRANKED"
        queue = ranked_queues[0]
        tier = queue.get("tier") or "UNRANKED"
        division = queue.get("division")
        queue_type = queue.get("type") or "Rank"
        label = f"{tier} {division}" if division else tier
        return f"{queue_type}  {label}"

    def _format_summoner_name(self, summoner: dict) -> str:
        name = summoner.get("name")
        tag = summoner.get("tag")
        if name and tag:
            return f"{name}#{tag}"
        return name or "-"

    def _filtered_champions(self) -> list[dict]:
        champions = (self.account.get("collection") or {}).get("champions") or []
        query = self.query_one("#detail-champions-search", Input).value.strip().lower()
        if not query:
            return champions
        return [
            champion
            for champion in champions
            if query in (champion.get("name") or "").lower()
            or query in (champion.get("alias") or "").lower()
            or query in (champion.get("title") or "").lower()
        ]

    def _filtered_skins(self) -> list[dict]:
        skins = (self.account.get("collection") or {}).get("skins") or []
        query = self.query_one("#detail-skins-search", Input).value.strip().lower()
        if not query:
            return skins
        return [
            skin
            for skin in skins
            if query in (skin.get("name") or "").lower()
            or query in (skin.get("description") or "").lower()
        ]

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "detail-champions-search":
            self._populate_champions_table()
        elif event.input.id == "detail-skins-search":
            self._populate_skins_table()

    def action_close_screen(self) -> None:
        self.app.pop_screen()


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

    #summoner-panel {
        width: 1fr;
    }

    #rank-panel {
        width: 1fr;
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


if __name__ == "__main__":
    app = Hexvault()
    app.run()
