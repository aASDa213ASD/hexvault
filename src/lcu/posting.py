from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import httpx
from posting.app import MainScreen
from posting.collection import Collection
from posting.config import SETTINGS, Settings
from posting.variables import load_variables
from textual.reactive import reactive
from textual.widget import Widget

from src.lcu.client import get_lcu_process_config


ROOT_DIR = Path(__file__).resolve().parents[2]
POSTING_DIR = ROOT_DIR / "var" / "posting" / "lcu"
COLLECTION_DIR = POSTING_DIR / "collection"
ENV_PATH = POSTING_DIR / "lcu.env"


@dataclass
class LcuPostingWorkspace:
    collection: Collection
    environment_files: tuple[Path, ...]
    settings: Settings
    status: str


class EmbeddedPostingMain(Widget, inherit_bindings=False):
    AUTO_FOCUS = MainScreen.AUTO_FOCUS
    BINDING_GROUP_TITLE = MainScreen.BINDING_GROUP_TITLE
    BINDINGS = MainScreen.BINDINGS

    selected_method = reactive("GET", init=False)
    current_layout = reactive("vertical", init=False)
    expanded_section = reactive(None, init=False)
    _jumping = reactive(False, init=False, bindings=True)

    compose = MainScreen.compose
    get_and_run_script = MainScreen.get_and_run_script
    send_request = MainScreen.send_request
    send_via_worker = MainScreen.send_via_worker
    on_method_selector_changed = MainScreen.on_method_selector_changed
    handle_submit_via_event = MainScreen.handle_submit_via_event
    on_response_received = MainScreen.on_response_received
    on_request_selected = MainScreen.on_request_selected
    on_request_cache_updated = MainScreen.on_request_cache_updated
    on_url_param_jump = MainScreen.on_url_param_jump
    on_path_param_jump = MainScreen.on_path_param_jump
    on_path_param_renamed = MainScreen.on_path_param_renamed
    watch_current_layout = MainScreen.watch_current_layout
    watch_expanded_section = MainScreen.watch_expanded_section
    action_send_request = MainScreen.action_send_request
    action_change_method = MainScreen.action_change_method
    action_toggle_collection_browser = MainScreen.action_toggle_collection_browser
    action_toggle_expanded = MainScreen.action_toggle_expanded
    expand_section = MainScreen.expand_section
    focus_within_request = MainScreen.focus_within_request
    focus_within_response = MainScreen.focus_within_response
    action_save_request = MainScreen.action_save_request
    action_new_request = MainScreen.action_new_request
    on_request_body_change = MainScreen.on_request_body_change
    on_content_changed = MainScreen.on_content_changed
    on_params_changed = MainScreen.on_params_changed
    on_path_params_changed = MainScreen.on_path_params_changed
    on_path_param_values_updated = MainScreen.on_path_param_values_updated
    on_url_changed = MainScreen.on_url_changed
    _sync_path_params_from_url = MainScreen._sync_path_params_from_url
    log_request_trace_event = MainScreen.log_request_trace_event
    action_open_request_search_palette = MainScreen.action_open_request_search_palette
    action_toggle_jump_mode = MainScreen.action_toggle_jump_mode
    watch__jumping = MainScreen.watch__jumping
    build_request_model = MainScreen.build_request_model
    build_httpx_request = MainScreen.build_httpx_request
    load_request_model = MainScreen.load_request_model
    on_curl_message = MainScreen.on_curl_message
    url_bar = MainScreen.url_bar
    footer = MainScreen.footer
    method_selector = MainScreen.method_selector
    url_input = MainScreen.url_input
    request_editor = MainScreen.request_editor
    response_area = MainScreen.response_area
    request_body_text_area = MainScreen.request_body_text_area
    headers_table = MainScreen.headers_table
    params_table = MainScreen.params_table
    path_params_table = MainScreen.path_params_table
    app_body = MainScreen.app_body
    app_header = MainScreen.app_header
    request_options = MainScreen.request_options
    request_metadata = MainScreen.request_metadata
    collection_browser = MainScreen.collection_browser
    request_auth = MainScreen.request_auth
    request_scripts = MainScreen.request_scripts
    collection_tree = MainScreen.collection_tree
    response_trace = MainScreen.response_trace
    response_script_output = MainScreen.response_script_output

    def __init__(
        self,
        collection: Collection,
        layout: str,
        environment_files: tuple[Path, ...],
    ) -> None:
        super().__init__()
        self.collection = collection
        self.cookies: httpx.Cookies = httpx.Cookies()
        self._initial_layout = layout
        self.environment_files = environment_files
        self.settings = SETTINGS.get()
        self.jumper = None
        self.posting = cast("object", self.app)
        self.styles.width = "1fr"
        self.styles.height = "1fr"

    def on_mount(self) -> None:
        MainScreen.on_mount(self)  # type: ignore[arg-type]
        MainScreen.on_screen_resume(self)  # type: ignore[arg-type]

    def set_focus(self, widget: Widget | None, scroll_visible: bool = True) -> None:
        self.app.set_focus(widget, scroll_visible=scroll_visible)


def build_lcu_posting_workspace() -> LcuPostingWorkspace:
    status = refresh_lcu_posting_credentials()
    _write_collection()

    env_paths = (ENV_PATH.resolve(),)
    settings = Settings(
        _env_file=env_paths,  # type: ignore[call-arg]
        heading={"visible": False},
        watch_env_files=False,
        watch_collection_files=False,
        watch_themes=False,
        load_user_themes=False,
        load_builtin_themes=True,
        theme="galaxy",
        spacing="compact",
    )
    SETTINGS.set(settings)
    load_variables(env_paths, settings.use_host_environment, avoid_cache=True)

    return LcuPostingWorkspace(
        collection=Collection.from_directory(str(COLLECTION_DIR.resolve())),
        environment_files=env_paths,
        settings=settings,
        status=status,
    )


def create_lcu_posting_screen_for_workspace(
    workspace: LcuPostingWorkspace,
) -> EmbeddedPostingMain:
    SETTINGS.set(workspace.settings)
    return EmbeddedPostingMain(
        collection=workspace.collection,
        layout=workspace.settings.layout,
        environment_files=workspace.environment_files,
    )


def refresh_lcu_posting_workspace(workspace: LcuPostingWorkspace) -> str:
    status = refresh_lcu_posting_credentials()
    SETTINGS.set(workspace.settings)
    load_variables(
        workspace.environment_files,
        workspace.settings.use_host_environment,
        avoid_cache=True,
    )
    workspace.status = status
    return status


def refresh_lcu_posting_credentials() -> str:
    config = get_lcu_process_config()
    POSTING_DIR.mkdir(parents=True, exist_ok=True)

    if not config:
        ENV_PATH.write_text(
            "\n".join(
                [
                    "LCU_BASE_URL=https://127.0.0.1:0",
                    "LCU_PASSWORD=",
                    "RIOT_CLIENT_BASE_URL=https://127.0.0.1:0",
                    "RIOT_CLIENT_PASSWORD=",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return "LeagueClientUx.exe not found. Start League Client, then refresh LCU."

    league_client = config.league_client
    riot_client = config.riot_client

    ENV_PATH.write_text(
        "\n".join(
            [
                f"LCU_BASE_URL={league_client.base_url if league_client else 'https://127.0.0.1:0'}",
                f"LCU_PASSWORD={league_client.password if league_client else ''}",
                f"RIOT_CLIENT_BASE_URL={riot_client.base_url if riot_client else 'https://127.0.0.1:0'}",
                f"RIOT_CLIENT_PASSWORD={riot_client.password if riot_client else ''}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    loaded = []
    if league_client:
        loaded.append(f"LCU {league_client.base_url}")
    if riot_client:
        loaded.append(f"Riot Client {riot_client.base_url}")
    return "Credentials loaded for " + ", ".join(loaded) + "."


def _write_collection() -> None:
    COLLECTION_DIR.mkdir(parents=True, exist_ok=True)
    requests = [
        ("Summoner", "current-summoner", "GET", "/lol-summoner/v1/current-summoner"),
        (
            "Summoner",
            "current-summoner-icon",
            "PUT",
            "/lol-summoner/v1/current-summoner/icon",
            {"profileIconId": 1},
        ),
        ("Session", "region-locale", "GET", "/riotclient/region-locale"),
        ("Riot Client", "ux-state", "GET", "/riotclient/ux-state"),
        (
            "Ranked",
            "current-ranked-stats",
            "GET",
            "/lol-ranked/v1/current-ranked-stats",
        ),
        ("Inventory", "wallet", "GET", "/lol-inventory/v1/wallet/rp"),
        ("Inventory", "owned-loot", "GET", "/lol-loot/v1/player-loot"),
        (
            "Collection",
            "owned-champions",
            "GET",
            "/lol-champions/v1/owned-champions-minimal",
        ),
        (
            "Collection",
            "owned-skins",
            "GET",
            "/lol-inventory/v2/inventory/CHAMPION_SKIN",
        ),
        (
            "Matchmaking",
            "search-state",
            "GET",
            "/lol-lobby/v2/lobby/matchmaking/search-state",
        ),
        (
            "Matchmaking",
            "accept-ready-check",
            "POST",
            "/lol-matchmaking/v1/ready-check/accept",
        ),
        (
            "Challenges",
            "clear-player-preferences",
            "POST",
            "/lol-challenges/v1/update-player-preferences/",
            {"challengeIds": []},
        ),
        (
            "Champ Select",
            "dodge-champ-select",
            "POST",
            (
                "/lol-login/v1/session/invoke"
                '?destination=lcdsServiceProxy&method=call&args=["","teambuilder-draft","quitV2",""]'
            ),
            {},
        ),
        ("Manual", "league-client-scratch", "GET", "/lol-summoner/v1/current-summoner"),
        ("Manual", "riot-client-scratch", "GET", "/riotclient/region-locale"),
    ]

    for request in requests:
        folder, name, method, path, *body = request
        _write_request(folder, name, method, path, body[0] if body else None)


def _write_request(
    folder: str,
    name: str,
    method: str,
    path: str,
    body: dict | None = None,
) -> None:
    is_riot_client = path.startswith("/riotclient/")
    base_url_variable = "RIOT_CLIENT_BASE_URL" if is_riot_client else "LCU_BASE_URL"
    password_variable = "RIOT_CLIENT_PASSWORD" if is_riot_client else "LCU_PASSWORD"
    url = f"${base_url_variable}{path}"
    lines = [
        f"name: {_yaml_scalar(name)}",
        f"description: {_yaml_scalar(f'LCU {method} {path}')}",
        f"method: {method}",
        f"url: {_yaml_scalar(url)}",
        "auth:",
        "  type: basic",
        "  basic:",
        "    username: riot",
        f"    password: ${password_variable}",
        "headers:",
        "- name: Accept",
        "  value: application/json",
        "- name: User-Agent",
        "  value: LeagueOfLegendsClient",
    ]
    if body is not None:
        lines.extend(
            [
                "- name: Content-Type",
                "  value: application/json",
                "body:",
                "  content: |-",
                *[f"    {line}" for line in json.dumps(body, indent=2).splitlines()],
                "  content_type: application/json",
            ]
        )
    lines.extend(
        [
            "options:",
            "  verify_ssl: false",
            "  timeout: 5.0",
            "",
        ]
    )

    request_path = COLLECTION_DIR / folder / f"{name}.posting.yaml"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text("\n".join(lines), encoding="utf-8")


def _yaml_scalar(value: str) -> str:
    return json.dumps(value)
