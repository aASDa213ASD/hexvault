from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


class AccountCredentialsScreen(ModalScreen[tuple[str, str] | None]):
    CSS = """
    AccountCredentialsScreen {
        align: center middle;
    }

    #credentials-dialog {
        width: 64;
        height: auto;
        padding: 1 2;
        border: round $surface;
    }

    #credentials-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #credentials-error {
        color: $error;
        margin-top: 1;
        min-height: 1;
    }

    #credentials-actions {
        margin-top: 1;
        align-horizontal: right;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="credentials-dialog"):
            yield Static("Add New Account Credentials", id="credentials-title")
            yield Input(placeholder="Login", id="credentials-login", compact=True)
            yield Static("")
            yield Input(placeholder="Password", password=True, id="credentials-password", compact=True)
            yield Static("", id="credentials-error")
            with Horizontal(id="credentials-actions"):
                yield Button("Cancel", id="credentials-cancel", compact=True)
                yield Button("Save", variant="primary", id="credentials-save", compact=True)

    def on_mount(self) -> None:
        self.query_one("#credentials-login", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "credentials-cancel":
            self.dismiss(None)
            return
        if event.button.id == "credentials-save":
            self._submit()

    def on_input_submitted(self, _: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        login = self.query_one("#credentials-login", Input).value.strip()
        password = self.query_one("#credentials-password", Input).value.strip()
        if not login or not password:
            self.query_one("#credentials-error", Static).update(
                "Login and password are required."
            )
            return
        self.dismiss((login, password))
