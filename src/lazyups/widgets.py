"""Reusable widgets for LazyUPS Textual app."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.validation import Integer
from textual.widgets import Button, Input, Static

from .models import Endpoint


class EndpointRow(Static):
    """Row for displaying an endpoint."""

    class Remove(Message):
        """Message emitted when a row requests removal."""

        def __init__(self, endpoint: Endpoint) -> None:
            super().__init__()
            self.endpoint = endpoint

    class Edit(Message):
        """Message emitted when a row requests editing."""

        def __init__(self, endpoint: Endpoint) -> None:
            super().__init__()
            self.endpoint = endpoint

    endpoint = reactive[Endpoint | None](None)

    def __init__(self, endpoint: Endpoint) -> None:
        super().__init__(classes="endpoint-row")
        self.endpoint = endpoint

    def compose(self) -> ComposeResult:
        assert self.endpoint is not None
        name_display = self.endpoint.name or "(unnamed)"
        yield Static(name_display, classes="endpoint-name")
        yield Static(self.endpoint.host, classes="endpoint-host")
        yield Static(str(self.endpoint.port), classes="endpoint-port")
        with Static(classes="endpoint-actions"):
            yield Button("Edit", variant="primary", classes="edit-endpoint")
            yield Button("Remove", variant="error", classes="remove-endpoint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if self.endpoint is None:
            return
        if "edit-endpoint" in event.button.classes:
            self.post_message(self.Edit(self.endpoint))
        elif "remove-endpoint" in event.button.classes:
            self.post_message(self.Remove(self.endpoint))


class EndpointForm(Static):
    """Form for adding or editing an endpoint."""

    class Submitted(Message):
        """Message emitted when the form is submitted."""

        def __init__(self, endpoint: Endpoint, *, previous: Endpoint | None = None) -> None:
            super().__init__()
            self.endpoint = endpoint
            self.previous = previous

    endpoint = reactive[Endpoint | None](None)

    def compose(self) -> ComposeResult:
        self.name_input = Input(placeholder="Friendly name (optional)", id="endpoint-name")
        self.host_input = Input(placeholder="Host", id="endpoint-host")
        self.port_input = Input(
            placeholder="Port (default 3493)",
            id="endpoint-port",
            validators=[Integer(minimum=1, maximum=65535)],
        )
        yield self.name_input
        yield self.host_input
        yield self.port_input
        self.submit_button = Button("Add Endpoint", variant="success", id="submit-endpoint")
        yield self.submit_button

    def reset_errors(self) -> None:
        for field in (self.host_input, self.port_input):
            field.border_title = ""
            field.remove_class("error")

    def load_endpoint(self, endpoint: Endpoint | None) -> None:
        self.endpoint = endpoint
        if endpoint is None:
            self.name_input.value = ""
            self.host_input.value = ""
            self.port_input.value = ""
            self.submit_button.label = "Add Endpoint"
            self.submit_button.variant = "success"
        else:
            self.name_input.value = endpoint.name or ""
            self.host_input.value = endpoint.host
            self.port_input.value = str(endpoint.port)
            self.submit_button.label = "Save Changes"
            self.submit_button.variant = "primary"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "submit-endpoint":
            return
        self.reset_errors()
        name = self.name_input.value.strip() or None
        host = self.host_input.value.strip()
        port_value = self.port_input.value.strip() or "3493"
        if not host:
            self.host_input.border_title = "Host required"
            self.host_input.add_class("error")
            return
        try:
            port = int(port_value)
        except ValueError:
            self.port_input.border_title = "Invalid port"
            self.port_input.add_class("error")
            return
        if not (1 <= port <= 65535):
            self.port_input.border_title = "Port out of range"
            self.port_input.add_class("error")
            return
        endpoint = Endpoint(host=host, port=port, name=name)
        self.post_message(self.Submitted(endpoint, previous=self.endpoint))
        if self.endpoint is None:
            self.load_endpoint(None)


__all__ = ["EndpointRow", "EndpointForm"]
