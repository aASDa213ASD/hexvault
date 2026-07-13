from __future__ import annotations

import webbrowser
from urllib.parse import quote

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Input,
    Static,
    TabbedContent,
    TabPane,
)

from src.ui.privacy import (
    fake_rank_for_account,
    fake_region_for_summoner,
    fake_username_for_summoner,
)
from src.ui.theme import HEXVAULT_THEME, ICON_SIZE
from src.ui.widgets.remote_image import RemoteImage
from src.usecases.accounts import delete_account

from pyperclip import copy as copy_to_clipboard

class ConfirmAccountRemovalScreen(ModalScreen[bool]):
    CSS = """
    ConfirmAccountRemovalScreen {
        align: center middle;
    }

    #confirm-remove-dialog {
        width: 70;
        max-height: 10;
        padding: 1 2;
        border: round $surface;
    }

    #confirm-remove-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #confirm-remove-actions {
        margin-top: 1;
        align-horizontal: right;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-remove-dialog"):
            yield Static("Forget this account?", id="confirm-remove-title")
            yield Static("This account will be permanently removed and this action is irreversable. Continue anyway?")
            with Horizontal(id="confirm-remove-actions"):
                yield Button("Cancel", id="remove-cancel", compact=True)
                yield Button("Proceed", id="remove-confirm", variant="error", compact=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "remove-confirm":
            self.dismiss(True)
            return
        
        self.dismiss(False)


class AccountDetailScreen(Screen[bool | None]):
    BINDINGS = [
        ("q", "close_screen", "Back"),
        ("r", "remove_account", "Forget account"),
    ]
    CSS = """
    #detail-root {
        height: 1fr;
        padding: 1 2;
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

    #detail-hero {
        height: 10;
    }

    #detail-icon-panel {
        width: 20;
        height: 10;
        border: round $surface-lighten-2;
        border-title-align: right;
        border-title-color: $text-muted;
        padding: 0 1;
        align-horizontal: center;
    }

    #detail-account-icon {
        width: 16;
        height: auto;
    }

    #detail-credentials-panel {
        width: 36;
        height: 10;
        border: round $surface-lighten-2;
        border-title-align: center;
        border-title-color: $text-muted;
        padding: 1 2;
        align-vertical: middle;
    }

    #detail-profile-panel {
        width: 1fr;
        height: 10;
        border: round $surface-lighten-2;
        border-title-align: center;
        border-title-color: $text-muted;
        padding: 1 2;
    }

    #detail-collection-panel {
        width: 1fr;
        height: 10;
        border: round $surface-lighten-2;
        border-title-align: center;
        border-title-color: $text-muted;
        padding: 1 2;
    }

    #detail-quick-stats {
        margin-top: 1;
        color: $text-muted;
        text-wrap: nowrap;
    }

    .muted {
        color: $text-muted;
    }

    .overview-row {
        height: 1;
    }

    .overview-label {
        width: auto;
        margin-right: 1;
        color: $text-muted;
        text-wrap: nowrap;
    }

    .overview-value {
        width: 1fr;
        text-style: bold;
        color: $primary;
        text-wrap: nowrap;
    }

    .detail-search {
        margin-top: 0;
    }

    #detail-items {
        height: 1fr;
    }

    .detail-table {
        height: 1fr;
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
        
        with VerticalScroll(id="detail-root"):
            with Horizontal(id="detail-hero"):
                with Vertical(id="detail-icon-panel") as panel:
                    panel.border_title = self._format_summoner_name(summoner)
                    yield RemoteImage(
                        summoner.get("icon_url"),
                        resize=ICON_SIZE,
                        empty_text="No icon available",
                        id="detail-account-icon",
                    )
                
                with Vertical(id="detail-credentials-panel") as panel:
                    panel.border_title = "Credentials"
                    with Horizontal():
                        with Vertical():
                            yield Button("Login", id="copy-login", compact=False)
                            yield Button("Password", id="copy-password", compact=False)
                        with Vertical():
                            yield Button("IDs", id="copy-ids", compact=False)
                            yield Button("OP.GG", id="open-opgg", compact=False)
                
                with Vertical(id="detail-profile-panel") as panel:
                    panel.border_title = "Profile"
                    yield from self._compose_overview_profile()
                    yield from self._compose_overview_ranked()
                
                with Vertical(id="detail-collection-panel") as panel:
                    panel.border_title = "Collection"
                    yield from self._compose_overview_currencies()
                    yield from self._compose_overview_collection()
            
            with TabbedContent(initial="champions", classes="section", id="detail-items") as panel:
                panel.border_title = "Items"
                panel.border_subtitle = "Table of posessions"
                with TabPane("Champions", id="champions"):
                    yield Input(
                        placeholder="Search champions...",
                        id="detail-champions-search",
                        compact=True,
                        classes="detail-search",
                    )
                    yield DataTable(id="detail-champions-table", classes="detail-table")
                
                with TabPane("Skins", id="skins"):
                    yield Input(
                        placeholder="Search skins...",
                        id="detail-skins-search",
                        compact=True,
                        classes="detail-search",
                    )
                    yield DataTable(id="detail-skins-table", classes="detail-table")
                
                with TabPane("Loot", id="loot"):
                    yield DataTable(id="detail-loot-table", classes="detail-table")
        
        yield Footer()

    def on_mount(self) -> None:
        self.app.register_theme(HEXVAULT_THEME)
        self.app.theme = "hexvault"
        self._populate_champions_table()
        self._populate_skins_table()
        self._populate_loot_table()

    def _compose_overview_profile(self) -> ComposeResult:
        summoner = self.account.get("summoner") or {}
        verification = self.account.get("verification") or {}
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
        table.add_columns("Champion ID", "Name", "Alias", "Purchased")
        champions = self._filtered_champions()
        if not champions:
            table.add_row("-", "No champions found", "-", "-")
            return
        
        for champion in champions:
            table.add_row(
                champion.get("champion_id") or "-",
                champion.get("name") or "-",
                champion.get("alias") or "-",
                champion.get("purchased") or "-",
            )

    def _populate_skins_table(self) -> None:
        table = self.query_one("#detail-skins-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Skin ID", "Name", "Purchased")
        skins = self._filtered_skins()
        if not skins:
            table.add_row("-", "No skins found", "-")
            return
        
        for skin in skins:
            table.add_row(
                skin.get("skin_id") or "-",
                skin.get("name") or "-",
                skin.get("purchased") or "-",
            )

    def _populate_loot_table(self) -> None:
        table = self.query_one("#detail-loot-table", DataTable)
        table.add_columns("Type", "Name", "Amount", "Disenchant")
        loot = self.account.get("loot") or {}
        champion_shards = loot.get("champion_shards") or []
        skin_shards = loot.get("skin_shards") or []
        
        entries = [("Champion", shard) for shard in champion_shards] + [("Skin", shard) for shard in skin_shards]
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
            if query in (champion.get("alias") or "").lower()
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
        ]

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "detail-champions-search":
            self._populate_champions_table()
        elif event.input.id == "detail-skins-search":
            self._populate_skins_table()

    def action_close_screen(self) -> None:
        self.dismiss(None)

    def action_remove_account(self) -> None:
        self.app.push_screen(
            ConfirmAccountRemovalScreen(),
            callback=self._on_remove_confirmation,
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        credentials = self.account.get("credentials") or {}
        summoner = self.account.get("summoner") or {}
        copy_value = ""

        if event.button.id == "copy-login":
            copy_value = str(credentials.get("login") or "")
        elif event.button.id == "copy-password":
            copy_value = str(credentials.get("password") or "")
        elif event.button.id == "copy-ids":
            ids = [
                f"account_id: {str(summoner.get('summoner_account_id') or '-')}",
                f"summoner_id: {str(summoner.get('summoner_id') or '-')}",
                f"puuid: {str(summoner.get('puuid') or '-')}",
            ]
            copy_value = "\n".join(ids)
        elif event.button.id == "open-opgg":
            name = str(summoner.get("name") or "").strip()
            tag = str(summoner.get("tag") or "").strip()
            region = str(summoner.get("region") or "").strip()
            if name and tag and region:
                url_name = quote(name, safe="")
                url_tag = quote(tag, safe="")
                url_region = quote(region.lower(), safe="")
                webbrowser.open(
                    f"https://op.gg/en/lol/summoners/{url_region}/{url_name}-{url_tag}",
                    new=2,
                )
            return
        else:
            return

        if not copy_value:
            return

        copy_to_clipboard(copy_value)

    def _on_remove_confirmation(self, confirmed: bool | None) -> None:
        if not confirmed:
            return

        account_id = self.account.get("id")
        if not isinstance(account_id, int):
            return

        try:
            delete_account(account_id)
            self.dismiss(True)
        except Exception:
            pass
