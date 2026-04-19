from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Rule,
    Static,
    TabbedContent,
    TabPane,
)

from src.ui.anonymization import (
    fake_rank_for_account,
    fake_region_for_summoner,
    fake_username_for_summoner,
)
from src.ui.widgets.remote_image import RemoteImage

ICON_SIZE = (16, 16)


class AccountDetailScreen(Screen[None]):
    BINDINGS = [("escape", "close_screen", "Back"), ("q", "close_screen", "Back")]
    CSS = """
    #detail-root {
        padding: 1 2;
    }

    #detail-hero {
        min-height: 10;
        max-height: 10;
    }

    #detail-account-icon {
        width: 16;
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

    .overview-section-title {
        margin-top: 2;
        margin-bottom: 1;
    }

    .overview-row {
        max-height: 1;
    }

    .overview-label {
        width: 18;
        color: $text-muted;
    }

    .overview-value {
        width: 1fr;
        text-style: bold;
    }
    """

    def __init__(
        self,
        account: dict,
        hide_names: bool = False,
        hide_regions: bool = False,
        randomize_ranks: bool = False,
    ) -> None:
        super().__init__()
        self.account = account
        self.hide_names = hide_names
        self.hide_regions = hide_regions
        self.randomize_ranks = randomize_ranks

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
                        f"{self._format_region(summoner)}  Level {summoner.get('level') or '-'}",
                        classes="muted",
                    )
                    yield Rule()
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
                    with Vertical():
                        yield Static("Profile", classes="overview-section-title")
                        yield Rule()
                        yield from self._compose_overview_profile()
                        yield Static("Currencies", classes="overview-section-title")
                        yield Rule()
                        yield from self._compose_overview_currencies()
                        yield Static("Collection", classes="overview-section-title")
                        yield Rule()
                        yield from self._compose_overview_collection()
                        yield Static("Ranked Queues", classes="overview-section-title")
                        yield Rule()
                        yield from self._compose_overview_ranked()
                with TabPane("Champions", id="champions"):
                    yield Input(
                        placeholder="Search champions...",
                        id="detail-champions-search",
                        compact=True,
                    )
                    yield DataTable(id="detail-champions-table", classes="detail-table")
                with TabPane("Skins", id="skins"):
                    yield Input(
                        placeholder="Search skins...",
                        id="detail-skins-search",
                        compact=True,
                    )
                    yield DataTable(id="detail-skins-table", classes="detail-table")
                with TabPane("Loot", id="loot"):
                    yield DataTable(id="detail-loot-table", classes="detail-table")
        yield Footer()

    def on_mount(self) -> None:
        self._populate_champions_table()
        self._populate_skins_table()
        self._populate_loot_table()

    def _compose_overview_profile(self) -> ComposeResult:
        summoner = self.account.get("summoner") or {}
        verification = self.account.get("verification") or {}
        credentials = self.account.get("credentials") or {}
        email_value = verification.get("email") or "-"
        if verification.get("is_email_verified") is not None:
            verified = "verified" if verification.get("is_email_verified") else "unverified"
            email_value = f"{email_value} ({verified})"
        yield self._overview_row("Account ID", str(self.account.get("id", "-")))
        yield self._overview_row("Region", self._format_region(summoner))
        yield self._overview_row("Level", str(summoner.get("level") or "-"))
        yield self._overview_row("Email", email_value)

    def _compose_overview_currencies(self) -> ComposeResult:
        loot = self.account.get("loot") or {}
        yield self._overview_row("Blue Essence", str(loot.get("blue_essence") or 0))
        yield self._overview_row("Orange Essence", str(loot.get("orange_essence") or 0))
        yield self._overview_row("Riot Points", str(loot.get("riot_points") or 0))

    def _compose_overview_collection(self) -> ComposeResult:
        collection = self.account.get("collection") or {}
        champions = collection.get("champions") or []
        skins = collection.get("skins") or []
        yield self._overview_row("Champions", str(len(champions)))
        yield self._overview_row("Skins", str(len(skins)))

    def _compose_overview_ranked(self) -> ComposeResult:
        ranked_queues = self._ranked_queues()
        if not ranked_queues:
            if self.randomize_ranks:
                fake_rank, fake_tier = fake_rank_for_account(self.account, "primary")
                yield self._overview_row("Queues", f"{fake_rank} {fake_tier}")
            else:
                yield self._overview_row("Queues", "No ranked data")
            return
        for index, queue in enumerate(ranked_queues):
            tier = queue.get("tier") or "UNRANKED"
            division = queue.get("division")
            label = f"{tier} {division}" if division else tier
            if self.randomize_ranks:
                queue_key = str(queue.get("type") or f"queue-{index}")
                fake_rank, fake_tier = fake_rank_for_account(self.account, queue_key)
                label = f"{fake_rank} {fake_tier}"
            summary = (
                f"{label}, {queue.get('league_points', 0)} LP, "
                f"{queue.get('wins', 0)}W/{queue.get('losses', 0)}L"
            )
            yield self._overview_row(queue.get("type") or "Rank", summary)

    def _overview_row(self, label: str, value: str) -> Horizontal:
        return Horizontal(
            Static(label, classes="overview-label"),
            Static(value, classes="overview-value"),
            classes="overview-row",
        )

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
        for _, shard in entries:
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
        if self.randomize_ranks:
            queue_key = str((ranked_queues[0] if ranked_queues else {}).get("type") or "primary")
            fake_rank, fake_tier = fake_rank_for_account(self.account, queue_key)
            if not ranked_queues:
                return f"{fake_rank} {fake_tier}"
            queue_type = ranked_queues[0].get("type") or "Rank"
            return f"{queue_type}  {fake_rank} {fake_tier}"
        if not ranked_queues:
            return "UNRANKED"
        queue = ranked_queues[0]
        tier = queue.get("tier") or "UNRANKED"
        division = queue.get("division")
        queue_type = queue.get("type") or "Rank"
        label = f"{tier} {division}" if division else tier
        return f"{queue_type}  {label}"

    def _format_summoner_name(self, summoner: dict) -> str:
        if self.hide_names:
            return fake_username_for_summoner(summoner)
        name = summoner.get("name")
        tag = summoner.get("tag")
        if name and tag:
            return f"{name}#{tag}"
        return name or "-"

    def _format_region(self, summoner: dict) -> str:
        if self.hide_regions:
            return fake_region_for_summoner(summoner)
        return summoner.get("region") or "-"

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
