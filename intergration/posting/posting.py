from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from src.lcu.client import get_lcu_process_config
from src.ui.theme import HEXVAULT_THEME_COLORS


ROOT_DIR = Path(__file__).resolve().parents[2]
POSTING_DIR = ROOT_DIR / "intergration" / "posting"
LCU_DIR = POSTING_DIR / "lcu"
COLLECTION_DIR = LCU_DIR / "collection"
ENV_PATH = LCU_DIR / "lcu.env"
CONFIG_PATH = LCU_DIR / "posting-config.yaml"
THEMES_DIR = LCU_DIR / "themes"
THEME_PATH = THEMES_DIR / "hexvault.yaml"
RUNNER_PATH = LCU_DIR / "run-posting.py"
RUNTIME_DIR = POSTING_DIR / "runtime"
RUNTIME_PYTHON = RUNTIME_DIR / "Scripts" / "python.exe"
LAUNCHER_PATH = LCU_DIR / "launch-posting.cmd"
POSTING_VERSION = "2.10.0"


@dataclass
class LcuPostingWorkspace:
    status: str
    collection_path: Path
    env_path: Path
    config_path: Path
    theme_path: Path
    runner_path: Path
    launcher_path: Path
    runtime_path: Path


def prepare_lcu_posting_workspace() -> LcuPostingWorkspace:
    status = refresh_lcu_posting_credentials()
    _write_collection()
    _write_theme_files()
    _write_runner()
    _write_launcher()
    return LcuPostingWorkspace(
        status=status,
        collection_path=COLLECTION_DIR,
        env_path=ENV_PATH,
        config_path=CONFIG_PATH,
        theme_path=THEME_PATH,
        runner_path=RUNNER_PATH,
        launcher_path=LAUNCHER_PATH,
        runtime_path=RUNTIME_DIR,
    )


def refresh_lcu_posting_workspace() -> str:
    status = refresh_lcu_posting_credentials()
    _write_collection()
    _write_theme_files()
    _write_runner()
    _write_launcher()
    return status


def run_lcu_posting_foreground() -> None:
    workspace = prepare_lcu_posting_workspace()
    env = os.environ.copy()
    env["HEXVAULT_PYTHON"] = sys.executable
    subprocess.run(
        [str(workspace.launcher_path)],
        cwd=ROOT_DIR,
        env=env,
        check=False,
    )


def refresh_lcu_posting_credentials() -> str:
    config = get_lcu_process_config()
    LCU_DIR.mkdir(parents=True, exist_ok=True)

    if not config:
        ENV_PATH.write_text("\n".join(
            [
                "LCU_BASE_URL=https://127.0.0.1:0",
                "LCU_PASSWORD=",
                "RIOT_CLIENT_BASE_URL=https://127.0.0.1:0",
                "RIOT_CLIENT_PASSWORD=",
                "",
            ]),
            encoding="utf-8",
        )
        return "FATAL: League Client and Riot Client not found, can not send requests to LCU or Riot API"

    league_client = config.league_client
    riot_client = config.riot_client

    ENV_PATH.write_text(
        "\n".join([
            f"LCU_BASE_URL={league_client.base_url if league_client else 'https://127.0.0.1:0'}",
            f"LCU_PASSWORD={league_client.password if league_client else ''}",
            f"RIOT_CLIENT_BASE_URL={riot_client.base_url if riot_client else 'https://127.0.0.1:0'}",
            f"RIOT_CLIENT_PASSWORD={riot_client.password if riot_client else ''}",
            "",
        ]),
        encoding="utf-8",
    )

    loaded = []
    if league_client:
        loaded.append(f"LCU {league_client.base_url}")
    
    if riot_client:
        loaded.append(f"Riot Client {riot_client.base_url}")
    
    return "Credentials loaded for " + ", ".join(loaded) + "."


def _write_launcher() -> None:
    LCU_DIR.mkdir(parents=True, exist_ok=True)
    LAUNCHER_PATH.write_text(
        "\n".join([
            "@echo off",
            "setlocal",
            'set "LCU_DIR=%~dp0"',
            'for %%I in ("%LCU_DIR%..") do set "POSTING_DIR=%%~fI"',
            'for %%I in ("%LCU_DIR%..\\..\\..") do set "ROOT_DIR=%%~fI"',
            'set "RUNTIME_DIR=%POSTING_DIR%\\runtime"',
            'set "RUNTIME_PYTHON=%RUNTIME_DIR%\\Scripts\\python.exe"',
            'set "COLLECTION_DIR=%LCU_DIR%collection"',
            'set "ENV_PATH=%LCU_DIR%lcu.env"',
            'set "POSTING_CONFIG_FILE=%LCU_DIR%posting-config.yaml"',
            'cd /d "%ROOT_DIR%"',
            'if not exist "%RUNTIME_PYTHON%" (',
            "  echo Creating isolated Posting runtime...",
            '  if defined HEXVAULT_PYTHON "%HEXVAULT_PYTHON%" -m venv "%RUNTIME_DIR%"',
            "  if errorlevel 1 if defined HEXVAULT_PYTHON goto :error",
            '  if not defined HEXVAULT_PYTHON py -3 -m venv "%RUNTIME_DIR%"',
            "  if errorlevel 1 python -m venv \"%RUNTIME_DIR%\"",
            "  if errorlevel 1 goto :error",
            ")",
            '"%RUNTIME_PYTHON%" -m pip show posting >nul 2>nul',
            "set POSTING_MISSING=%errorlevel%",
            '"%RUNTIME_PYTHON%" -m pip show psutil >nul 2>nul',
            "set PSUTIL_MISSING=%errorlevel%",
            "if not \"%POSTING_MISSING%%PSUTIL_MISSING%\"==\"00\" (",
            f'  "%RUNTIME_PYTHON%" -m pip install posting=={POSTING_VERSION} psutil^>=7.0.0',
            "  if errorlevel 1 goto :error",
            ")",
            '"%RUNTIME_PYTHON%" "%LCU_DIR%run-posting.py"',
            "goto :done",
            ":error",
            "echo Failed to start Posting.",
            "pause",
            ":done",
            "endlocal",
        ]),
        encoding="utf-8",
    )


def _write_runner() -> None:
    LCU_DIR.mkdir(parents=True, exist_ok=True)
    RUNNER_PATH.write_text(
        r'''
from __future__ import annotations

from pathlib import Path

import psutil
from posting.app import MainScreen, Posting
from posting.collection import Collection
from posting.config import Settings
from posting.variables import load_variables, update_variables
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button


LCU_DIR = Path(__file__).resolve().parent
COLLECTION_DIR = LCU_DIR / "collection"
ENV_PATH = LCU_DIR / "lcu.env"


def refresh_lcu_credentials() -> str:
    config = _read_lcu_process_config()
    if not config:
        ENV_PATH.write_text(
            "\n".join([
                    "LCU_BASE_URL=https://127.0.0.1:0",
                    "LCU_PASSWORD=",
                    "RIOT_CLIENT_BASE_URL=https://127.0.0.1:0",
                    "RIOT_CLIENT_PASSWORD=",
                    "",
            ]),
            encoding="utf-8",
        )
        return "League Client and Riot Client not found."

    league_client = config.get("league_client")
    riot_client = config.get("riot_client")
    ENV_PATH.write_text(
        "\n".join([
                f"LCU_BASE_URL={league_client['base_url'] if league_client else 'https://127.0.0.1:0'}",
                f"LCU_PASSWORD={league_client['password'] if league_client else ''}",
                f"RIOT_CLIENT_BASE_URL={riot_client['base_url'] if riot_client else 'https://127.0.0.1:0'}",
                f"RIOT_CLIENT_PASSWORD={riot_client['password'] if riot_client else ''}",
                "",
        ]),
        encoding="utf-8",
    )
    loaded = []
    if league_client:
        loaded.append(f"LCU {league_client['base_url']}")
    
    if riot_client:
        loaded.append(f"Riot Client {riot_client['base_url']}")
    
    return "Credentials loaded for " + ", ".join(loaded) + "."


def _read_lcu_process_config() -> dict | None:
    league_client = None
    riot_client = None

    for process in psutil.process_iter(["name", "cmdline"]):
        try:
            name = (process.info.get("name") or "").lower()
            if name not in {
                "leagueclientux.exe",
                "riot client.exe",
                "riotclientservices.exe",
            }:
                continue
            args = process.info.get("cmdline") or []
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue

        values = {}
        for arg in args:
            if not arg.startswith("--") or "=" not in arg:
                continue
            key, value = arg[2:].split("=", 1)
            values[key] = value

        if name == "leagueclientux.exe" and league_client is None:
            app_port = values.get("app-port")
            remoting_auth_token = values.get("remoting-auth-token")
            if app_port and remoting_auth_token:
                league_client = {
                    "base_url": f"https://127.0.0.1:{app_port}",
                    "password": remoting_auth_token,
                }

        if riot_client is None and name == "leagueclientux.exe":
            riot_app_port = values.get("riotclient-app-port")
            riot_auth_token = values.get("riotclient-auth-token")
            if riot_app_port and riot_auth_token:
                riot_client = {
                    "base_url": f"https://127.0.0.1:{riot_app_port}",
                    "password": riot_auth_token,
                }

        if riot_client is None and name != "leagueclientux.exe":
            app_port = values.get("app-port")
            remoting_auth_token = values.get("remoting-auth-token")
            if app_port and remoting_auth_token:
                riot_client = {
                    "base_url": f"https://127.0.0.1:{app_port}",
                    "password": remoting_auth_token,
                }
            else:
                riot_app_port = values.get("riotclient-app-port")
                riot_auth_token = values.get("riotclient-auth-token")
                if riot_app_port and riot_auth_token:
                    riot_client = {
                        "base_url": f"https://127.0.0.1:{riot_app_port}",
                        "password": riot_auth_token,
                    }

    if league_client or riot_client:
        return {"league_client": league_client, "riot_client": riot_client}
    
    return None


class HexvaultPostingScreen(MainScreen):
    def on_mount(self) -> None:
        super().on_mount()
        self.border_title = "League Client"
        self.border_subtitle = "LCU API Interface"

    def compose(self) -> ComposeResult:
        yield from super().compose()
        yield Button("Refresh LCU", id="hexvault-refresh-lcu")

    @on(Button.Pressed, "#hexvault-refresh-lcu")
    def refresh_lcu(self) -> None:
        status = refresh_lcu_credentials()
        load_variables(
            self.environment_files,
            self.settings.use_host_environment,
            avoid_cache=True,
        )
        update_variables(self.app.session_env)
        self.app.env_changed_signal.publish(None)
        self.notify(status, title="LCU refreshed", timeout=4)


class HexvaultPosting(Posting):
    BINDINGS = [
        Binding("ctrl+c", "ignore_ctrl_c", show=False, priority=True),
        Binding("q", "quit", "Quit"),
    ]

    CSS = """
    HexvaultPostingScreen {
        border: round $accent 40%;
        border-title-align: right;
        border-title-color: $text-accent 50%;
        border-subtitle-color: $text-muted;
        padding: 1 1;
    }

    HexvaultPostingScreen:focus-within {
        border: round $accent 100%;
        border-title-color: $foreground;
        border-title-style: bold;
    }

    #hexvault-refresh-lcu {
        width: 1fr;
        margin-top: 1;
    }
    """

    def get_default_screen(self) -> HexvaultPostingScreen:
        self.main_screen = HexvaultPostingScreen(
            collection=self.collection,
            layout=self.settings.layout,
            environment_files=self.environment_files,
        )
        return self.main_screen

    def action_ignore_ctrl_c(self) -> None:
        pass


def main() -> None:
    refresh_lcu_credentials()
    env_paths = (ENV_PATH.resolve(),)
    settings = Settings(_env_file=env_paths)
    load_variables(env_paths, settings.use_host_environment, avoid_cache=True)
    collection = Collection.from_directory(str(COLLECTION_DIR.resolve()))
    app = HexvaultPosting(settings, env_paths, collection, True)
    app.run()


if __name__ == "__main__":
    main()
'''.lstrip(),
        encoding="utf-8",
    )


def _write_theme_files() -> None:
    THEMES_DIR.mkdir(parents=True, exist_ok=True)
    theme_directory = _relative_to_root(THEMES_DIR)
    CONFIG_PATH.write_text(
        "\n".join([
            "theme: hexvault",
            f'theme_directory: "{theme_directory}"',
            "load_user_themes: true",
            "load_builtin_themes: true",
            "spacing: standard",
            "heading:",
            "  visible: false",
            "  show_version: false",
            "  show_host: false",
            "watch_themes: true",
            "watch_env_files: true",
            "watch_collection_files: true",
            "",
        ]),
        encoding="utf-8",
    )
    THEME_PATH.write_text(
        "\n".join([
            "name: hexvault",
            f"primary: '{HEXVAULT_THEME_COLORS['primary']}'",
            f"secondary: '{HEXVAULT_THEME_COLORS['secondary']}'",
            f"accent: '{HEXVAULT_THEME_COLORS['accent']}'",
            f"background: '{HEXVAULT_THEME_COLORS['background']}'",
            f"surface: '{HEXVAULT_THEME_COLORS['surface']}'",
            f"panel: '{HEXVAULT_THEME_COLORS['panel']}'",
            f"warning: '{HEXVAULT_THEME_COLORS['warning']}'",
            f"error: '{HEXVAULT_THEME_COLORS['error']}'",
            f"success: '{HEXVAULT_THEME_COLORS['success']}'",
            "dark: true",
            "text_area:",
            "  gutter: 'dim'",
            f"  cursor: 'reverse {HEXVAULT_THEME_COLORS['primary']}'",
            f"  cursor_line: 'on {HEXVAULT_THEME_COLORS['surface']}'",
            f"  selection: 'on {HEXVAULT_THEME_COLORS['secondary']}'",
            "syntax:",
            f"  json_key: '{HEXVAULT_THEME_COLORS['primary']}'",
            f"  json_string: '{HEXVAULT_THEME_COLORS['success']}'",
            f"  json_number: '{HEXVAULT_THEME_COLORS['warning']}'",
            f"  json_boolean: '{HEXVAULT_THEME_COLORS['secondary']}'",
            f"  json_null: '{HEXVAULT_THEME_COLORS['error']}'",
            "url:",
            f"  base: '{HEXVAULT_THEME_COLORS['secondary']}'",
            f"  protocol: 'bold {HEXVAULT_THEME_COLORS['accent']}'",
            "  separator: 'dim'",
            "variable:",
            f"  resolved: '{HEXVAULT_THEME_COLORS['success']}'",
            f"  unresolved: '{HEXVAULT_THEME_COLORS['error']}'",
            "",
        ]),
        encoding="utf-8",
    )


def _write_collection() -> None:
    COLLECTION_DIR.mkdir(parents=True, exist_ok=True)
    requests = [
        (
            "Summoner",
            "current-summoner",
            "GET",
            "/lol-summoner/v1/current-summoner"
        ),
        (
            "Summoner",
            "current-summoner-icon",
            "PUT",
            "/lol-summoner/v1/current-summoner/icon",
            {"profileIconId": 1}
        ),
        (
            "Riot Client",
            "region-locale",
            "GET",
            "/riotclient/region-locale"
        ),
        (
            "Ranked",
            "current-ranked-stats",
            "GET",
            "/lol-ranked/v1/current-ranked-stats"
        ),
        (
            "Account",
            "email-verification",
            "GET",
            "/lol-email-verification/v1/email"
        ),
        (
            "Account",
            "wallet",
            "GET",
            "/lol-inventory/v1/wallet/rp"
        ),
        (
            "Account",
            "owned-loot",
            "GET",
            "/lol-loot/v1/player-loot"
        ),
        (
            "Account",
            "owned-champions",
            "GET",
            "/lol-champions/v1/owned-champions-minimal"
        ),
        (
            "Account",
            "owned-skins",
            "GET",
            "/lol-inventory/v2/inventory/CHAMPION_SKIN"
        ),
        (
            "Matchmaking",
            "search-state",
            "GET",
            "/lol-lobby/v2/lobby/matchmaking/search-state"
        ),
        (
            "Matchmaking",
            "accept-ready-check",
            "POST",
            "/lol-matchmaking/v1/ready-check/accept"
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
        )
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


def _relative_to_root(path: Path) -> str:
    try:
        return path.relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return path.as_posix()
