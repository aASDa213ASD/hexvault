from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.worker import Worker, WorkerState
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    ProgressBar,
    Static,
    TabbedContent,
    Input,
    TextArea,
    Select,
)

from src.database.connection import init_db
from src.lcu.client import get_current_summoner
from intergration.posting.posting import (
    prepare_lcu_posting_workspace,
    run_lcu_posting_foreground,
)
from src.ui.shared.privacy import (
    fake_rank_for_account,
    fake_region_for_summoner,
    fake_username_for_summoner,
)
from src.ui.shared.image_cache import prewarm_images
from src.ui.screens.account_credentials import AccountCredentialsScreen
from src.ui.screens.account_detail import AccountDetailScreen
from src.ui.screens.tabs.accounts import compose_accounts_tab
from src.ui.screens.tabs.client import compose_client_tab
from src.ui.screens.tabs.health import compose_health_tab
from src.ui.screens.tabs.settings import compose_settings_tab
from src.ui.screens.tabs.search import compose_search_tab
from src.ui.shared.theme import (
    HEXVAULT_CSS,
    HEXVAULT_THEME,
    ICON_SIZE,
    RANK_COLORS,
)
from src.ui.widgets.remote_image import RemoteImage
from src.usecases.accounts import list_accounts
from src.usecases.search import search_accounts
from src.usecases.health import health
from src.usecases.lcu import (
    current_account_exists,
    get_current_account_from_lcu,
    save_current_account,
)


RANKS_DIR = Path(__file__).resolve().parents[3] / "resources" / "ranks"


@dataclass
class SyncResult:
    kind: str
    current: dict | None = None
    summoner: dict | None = None
    error: str | None = None


class SyncProgressScreen(ModalScreen[None]):
    CSS = """
    SyncProgressScreen {
        align: center middle;
    }

    #sync-progress-dialog {
        width: 52;
        max-height: 8;
        padding: 1 2;
        border: round $surface;
    }

    #sync-progress-title {
        text-style: bold;
    }

    #sync-progress-indicator {
        height: 1;
        margin-left: 6;
        margin-top: 1;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="sync-progress-dialog"):
            yield Static("This might take a moment", id="sync-progress-title")
            yield Static(self.message, id="sync-progress-body")
            yield ProgressBar(
                total=None,
                show_percentage=False,
                show_eta=False,
                id="sync-progress-indicator",
            )


class Hexvault(App):
    BINDINGS = [("q", "quit", "Quit")]
    CSS = HEXVAULT_CSS

    def __init__(self) -> None:
        self._posting_workspace = prepare_lcu_posting_workspace()
        self._active_sync_worker: Worker[SyncResult] | None = None
        self._active_health_worker: Worker[dict] | None = None
        self._decay_deadlines: dict[str, datetime] = {}
        self._sync_progress_screen: SyncProgressScreen | None = None
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="app-root"):
            with TabbedContent(initial="accounts"):
                yield from compose_accounts_tab()
                yield from compose_search_tab()
                yield from compose_client_tab()
                yield from compose_settings_tab()
                yield from compose_health_tab()
        
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(HEXVAULT_THEME)
        self.theme = "hexvault"
        init_db()
        self._accounts: list[dict] = []
        self._search_results: list[dict] = []
        self._populate_accounts_table()
        self._populate_search_results([])
        self._populate_lcu_status()
        self.set_interval(60, self._update_decay_countdowns, name="decay-countdown")

    def _populate_accounts_table(self) -> None:
        table = self.query_one("#accounts-table", DataTable)
        table.clear(columns=True)
        table.cursor_type = "row"
        table.add_column("ID")
        table.add_column("Summoner")
        table.add_column("Region")
        table.add_column("Level")
        table.add_column("Blue Essence")
        table.add_column("Rank")
        table.add_column("Decay", key="decay")
        table.add_column("Notes")
        self._decay_deadlines = {}

        self._accounts = list_accounts()
        if not self._accounts:
            self.query_one("#account-icon", RemoteImage).load_from_url(None)
            self.query_one("#account-region", Static).update("-")
            self.query_one("#account-level", Static).update("-")
            self.query_one("#blue-essence", Static).update("-")
            self.query_one("#riot-points", Static).update("-")
            self.query_one("#champions-count", Static).update("-")
            self.query_one("#skins-count", Static).update("-")
            table.add_row("-", "No accounts found", "-", "-", "-", "-", "-", "-")
            return

        icon_urls: list[str] = []
        for account in self._accounts:
            summoner = account.get("summoner") or {}
            icon_url = summoner.get("icon_url")
            if isinstance(icon_url, str):
                icon_urls.append(icon_url)

        prewarm_images(icon_urls, resize=ICON_SIZE)

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
            days_until_decay = primary_queue.get("days_until_decay")
            row_key = f"account-{account.get('id')}"
            decay_deadline = self._decay_deadline(primary_queue)
            if decay_deadline is not None:
                self._decay_deadlines[row_key] = decay_deadline

            table.add_row(
                Text(str(account.get("id", "")), style="dim"),
                Text(self._format_summoner_name(summoner), style="$primary"),
                Text(self._format_region(summoner), style="dim"),
                Text(str(summoner.get("level") or "-"), style="dim"),
                Text(str(loot.get("blue_essence") or "-"), style="#B2DCFF"),
                Text(rank_label, style=RANK_COLORS.get(rank_tier, "")),
                Text(
                    self._format_decay_countdown(decay_deadline),
                    style="#FFF4D0" if decay_deadline is not None else "dim",
                ),
                Text(
                    " ".join(str(account.get("notes") or "").splitlines()) or '',
                    style="dim",
                ),
                key=row_key,
            )

        self._show_account_details(self._accounts[0])

    def _decay_deadline(self, queue: dict) -> datetime | None:
        stored_deadline = queue.get("decay_deadline")
        if isinstance(stored_deadline, str):
            try:
                parsed = datetime.fromisoformat(
                    stored_deadline.replace("Z", "+00:00")
                )
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                pass

        days_until_decay = queue.get("days_until_decay")
        if days_until_decay is None:
            return None

        try:
            days = int(days_until_decay)
        except (TypeError, ValueError):
            return None

        now = datetime.now().astimezone()
        local_midnight = datetime.combine(
            now.date() + timedelta(days=max(days, 0)),
            time.min,
            tzinfo=now.tzinfo,
        )
        return local_midnight.astimezone(timezone.utc)

    def _format_decay_countdown(self, deadline: datetime | None) -> str:
        if deadline is None:
            return ""

        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        remaining = max(
            0,
            int((deadline - datetime.now(timezone.utc)).total_seconds()),
        )
        days, remainder = divmod(remaining, 86_400)
        hours, remainder = divmod(remainder, 3_600)
        minutes = remainder // 60
        seconds = remainder // 60
        return f"in {days}d {hours:02}h {minutes:02}m"

    def _update_decay_countdowns(self) -> None:
        if not self._decay_deadlines:
            return

        table = self.query_one("#accounts-table", DataTable)
        for row_key, deadline in self._decay_deadlines.items():
            table.update_cell(
                row_key,
                "decay",
                Text(self._format_decay_countdown(deadline), style="$warning"),
            )

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
        if event.data_table.id != "accounts-table":
            return
        if event.cursor_row < 0 or event.cursor_row >= len(self._accounts):
            return
        
        self._show_account_details(self._accounts[event.cursor_row])

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        accounts = self._search_results if event.data_table.id == "search-results" else self._accounts
        if event.data_table.id not in {"accounts-table", "search-results"}:
            return
        if event.cursor_row < 0 or event.cursor_row >= len(accounts):
            return
        
        self.push_screen(
            AccountDetailScreen(
                accounts[event.cursor_row],
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
        }:
            return

        selected_row = self.query_one("#accounts-table", DataTable).cursor_row
        self._populate_accounts_table()
        if 0 <= selected_row < len(self._accounts):
            self._show_account_details(self._accounts[selected_row])

    def on_tabbed_content_tab_activated(
        self,
        event: TabbedContent.TabActivated,
    ) -> None:
        if event.pane.id == "health":
            self._start_health_check()

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
        if event.button.id == "search-submit":
            self._run_search()
            return

        if event.button.id == "search-clear":
            self._clear_search()
            return

        if event.button.id == "open-posting-here":
            with self.suspend():
                run_lcu_posting_foreground()
            return

        if event.button.id != "lcu-sync":
            return
        
        self._start_sync_current_account()

    def _run_search(self) -> None:
        filters = {
            "region": self.query_one("#search-region", Input).value,
            "level_min": self.query_one("#search-level-min", Input).value,
            "level_max": self.query_one("#search-level-max", Input).value,
            "rank_min": self._search_select_value("#search-rank-min"),
            "rank_max": self._search_select_value("#search-rank-max"),
            "champions": self.query_one("#search-champions", Input).value,
            "skins": self.query_one("#search-skins", Input).value,
            "blue_essence_min": self.query_one("#search-be-min", Input).value,
            "riot_points_min": self.query_one("#search-rp-min", Input).value,
            "champion_shards": self.query_one("#search-champion-shards", Input).value,
            "skin_shards": self.query_one("#search-skin-shards", Input).value,
            "advanced": self.query_one("#search-advanced", TextArea).text,
        }
        try:
            results = search_accounts(filters)
        except ValueError as exc:
            self.query_one("#search-status", Static).update(f"Error: {exc}")
            return
        self._populate_search_results(results)
        self.query_one("#search-status", Static).update(f"{len(results)} account(s) found")

    def _populate_search_results(self, accounts: list[dict]) -> None:
        self._search_results = accounts
        table = self.query_one("#search-results", DataTable)
        table.clear(columns=True)
        table.cursor_type = "row"
        table.add_columns("ID", "Summoner", "Region", "Level", "Rank", "Blue Essence", "Champions", "Skins")
        if not accounts:
            table.add_row("-", "No matching accounts", "-", "-", "-", "-", "-", "-")
            return
        for account in accounts:
            summoner = account.get("summoner") or {}
            loot = account.get("loot") or {}
            collection = account.get("collection") or {}
            ranked_queues = (account.get("rank") or {}).get("ranked_queues") or []
            primary_queue = ranked_queues[0] if ranked_queues else {}
            rank_tier = primary_queue.get("tier") or "Unranked"
            rank_label = rank_tier
            if primary_queue.get("division"):
                rank_label = f"{rank_label} {primary_queue['division']}"
            table.add_row(
                str(account.get("id") or "-"),
                self._format_summoner_name(summoner),
                self._format_region(summoner),
                str(summoner.get("level") or "-"),
                Text(rank_label, style=RANK_COLORS.get(rank_tier, "")),
                str(loot.get("blue_essence") or 0),
                str(len(collection.get("champions") or [])),
                str(len(collection.get("skins") or [])),
            )

    def _clear_search(self) -> None:
        for input_widget in self.query("#search-filters Input"):
            input_widget.value = ""
        self.query_one("#search-rank-min", Select).value = Select.NULL
        self.query_one("#search-rank-max", Select).value = Select.NULL
        self.query_one("#search-advanced", TextArea).load_text("")
        self.query_one("#search-status", Static).update("")
        self._populate_search_results([])

    def _search_select_value(self, selector: str) -> str:
        value = self.query_one(selector, Select).value
        return value if isinstance(value, str) else ""

    def _start_sync_current_account(self) -> None:
        if self._active_sync_worker and not self._active_sync_worker.is_finished:
            return

        self._show_sync_progress("Requesting data from the League Client...")
        self._set_sync_button_enabled(False)
        self._set_lcu_sync_status("Syncing...")
        self._active_sync_worker = self._sync_current_account()

    @work(thread=True, exclusive=True, group="lcu-sync", exit_on_error=False)
    def _sync_current_account(self) -> SyncResult:
        try:
            current = get_current_account_from_lcu()
            exists = current_account_exists().get("exists", False)
            if not exists:
                return SyncResult(kind="credentials_required", current=current)

            save_current_account(overwrite=True)
            return SyncResult(
                kind="synced",
                current=current,
                summoner=get_current_summoner(),
            )
        except Exception as exc:
            return SyncResult(
                kind="error",
                error=f"fatal: {exc}",
                summoner=self._get_current_summoner_safely(),
            )

    @work(thread=True, exclusive=True, group="lcu-sync", exit_on_error=False)
    def _save_new_account_with_credentials_worker(
        self,
        current: dict,
        credentials: tuple[str, str],
    ) -> SyncResult:
        login, password = credentials
        try:
            save_current_account(login=login, password=password, overwrite=False)
            return SyncResult(
                kind="added",
                current=current,
                summoner=get_current_summoner(),
            )
        except Exception as exc:
            return SyncResult(
                kind="error",
                current=current,
                error=f"fatal: {exc}",
                summoner=self._get_current_summoner_safely(),
            )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker is self._active_health_worker:
            self._handle_health_worker_state(event)
            return

        if event.worker is not self._active_sync_worker:
            return

        if event.state not in {
            WorkerState.CANCELLED,
            WorkerState.ERROR,
            WorkerState.SUCCESS,
        }:
            return

        self._dismiss_sync_progress()
        self._set_sync_button_enabled(True)
        self._active_sync_worker = None

        result = event.worker.result
        if result is None:
            self._set_lcu_sync_status("fatal: Sync worker did not return a result")
            return

        self._handle_sync_result(result)

    def _handle_sync_result(self, result: SyncResult) -> None:
        if result.kind == "credentials_required":
            if result.current is None:
                self._set_lcu_sync_status("fatal: League Client account data missing")
                return

            current = result.current
            self.push_screen(
                AccountCredentialsScreen(),
                callback=lambda credentials: self._save_new_account_with_credentials(
                    current,
                    credentials,
                ),
            )
            return

        if result.kind in {"synced", "added"}:
            current = result.current or {}
            summoner = current.get("summoner") or {}
            name = self._format_summoner_name(summoner)
            action = "Account synced" if result.kind == "synced" else "Account added"
            self._populate_accounts_table()
            self._start_health_check()
            self._update_lcu_identity(result.summoner)
            self._set_lcu_sync_status(f"{action} - {name}")
            return

        self._update_lcu_identity(result.summoner)
        self._set_lcu_sync_status(result.error or "fatal: Sync failed")

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

        self._show_sync_progress("Saving new account...")
        self._set_sync_button_enabled(False)
        self._set_lcu_sync_status("Saving account...")
        self._active_sync_worker = self._save_new_account_with_credentials_worker(
            current,
            credentials,
        )

    def _show_sync_progress(self, message: str) -> None:
        self._dismiss_sync_progress()
        self._sync_progress_screen = SyncProgressScreen(message)
        self.push_screen(self._sync_progress_screen)

    def _dismiss_sync_progress(self) -> None:
        if self._sync_progress_screen is None:
            return

        try:
            self._sync_progress_screen.dismiss(None)
        except Exception:
            pass
        self._sync_progress_screen = None

    def _set_sync_button_enabled(self, enabled: bool) -> None:
        self.query_one("#lcu-sync", Button).disabled = not enabled

    def _update_lcu_identity(self, summoner: dict | None) -> None:
        self.query_one("#client-icon", RemoteImage).load_from_url(
            summoner.get("icon_url") if summoner else None
        )
        self._set_lcu_welcome(summoner)

    def _get_current_summoner_safely(self) -> dict | None:
        try:
            return get_current_summoner()
        except Exception:
            return None

    def _start_health_check(self) -> None:
        if self._active_health_worker and not self._active_health_worker.is_finished:
            return

        self._set_health_check_pending()
        self._active_health_worker = self._health_check_worker()

    @work(thread=True, exclusive=True, group="health", exit_on_error=False)
    def _health_check_worker(self) -> dict:
        return health()

    def _handle_health_worker_state(self, event: Worker.StateChanged) -> None:
        if event.state not in {
            WorkerState.CANCELLED,
            WorkerState.ERROR,
            WorkerState.SUCCESS,
        }:
            return

        self._active_health_worker = None

        if event.state != WorkerState.SUCCESS or event.worker.result is None:
            self._populate_health_status(
                {
                    "COMMUNITY_DRAGON": {
                        "ok": False,
                        "error": "Health check did not complete",
                    },
                    "LCU": {
                        "ok": False,
                        "error": "Health check did not complete",
                    },
                    "DB": {
                        "ok": False,
                        "error": "Health check did not complete",
                    },
                }
            )
            return

        self._populate_health_status(event.worker.result)

    def _set_health_check_pending(self) -> None:
        self.query_one("#health-overall-state", Static).update("Checking")
        self.query_one("#health-healthy-count", Static).update("-")
        self.query_one("#health-failing-count", Static).update("-")
        self._set_health_row_pending("community-dragon")
        self._set_health_row_pending("lcu")
        self._set_health_row_pending("db")

    def _set_health_row_pending(self, row_id: str) -> None:
        row = self.query_one(f"#health-check-{row_id}", Horizontal)
        state = self.query_one(f"#health-state-{row_id}", Static)
        detail_widget = self.query_one(f"#health-detail-{row_id}", Static)

        row.remove_class("ok")
        row.remove_class("fatal")
        state.remove_class("ok")
        state.remove_class("fatal")
        state.update("...")
        detail_widget.update("Checking...")

    def _populate_health_status(self, status: dict) -> None:
        healthy_count = sum(1 for result in status.values() if result.get("ok"))
        failing_count = len(status) - healthy_count

        overall_label = "Operational" if failing_count == 0 else "Degraded"
        self.query_one("#health-overall-state", Static).update(overall_label)
        self.query_one("#health-healthy-count", Static).update(str(healthy_count))
        self.query_one("#health-failing-count", Static).update(str(failing_count))

        self._set_health_row(
            "community-dragon",
            status.get("COMMUNITY_DRAGON") or {},
            ok_detail="Reachable",
        )
        self._set_health_row(
            "lcu",
            status.get("LCU") or {},
            ok_detail="Client session detected",
            fail_detail="Client is closed or not authenticated",
        )
        self._set_health_row(
            "db",
            status.get("DB") or {},
            ok_detail="Connection ready",
        )

    def _set_health_row(
        self,
        row_id: str,
        result: dict,
        *,
        ok_detail: str,
        fail_detail: str = "Unavailable",
    ) -> None:
        ok = bool(result.get("ok"))
        label = "OK" if ok else "Fatal"
        detail = ok_detail if ok else str(result.get("error") or fail_detail)
        status_code = result.get("status")
        if ok and status_code:
            detail = f"{detail} - HTTP {status_code}"

        row = self.query_one(f"#health-check-{row_id}", Horizontal)
        state = self.query_one(f"#health-state-{row_id}", Static)
        detail_widget = self.query_one(f"#health-detail-{row_id}", Static)

        row.set_class(ok, "ok")
        row.set_class(not ok, "fatal")
        state.set_class(ok, "ok")
        state.set_class(not ok, "fatal")
        state.update(label)
        detail_widget.update(detail)
