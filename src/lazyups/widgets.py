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


class MonitorFieldsForm(Static):
    """Form for selecting monitor columns."""

    class Submitted(Message):
        """Message emitted when monitor field selection is saved."""

        def __init__(self, fields: list[str]) -> None:
            super().__init__()
            self.fields = fields

    def __init__(
        self,
        *,
        grouped_options: list[tuple[str, list[tuple[str, str]]]],
        selected: list[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.grouped_options = grouped_options
        self.selected = set(selected or [])
        self.toggles: dict[str, bool] = {}
        self.labels: dict[str, str] = {}
        self.button_field_map: dict[str, str] = {}

    def _label(self, key: str, text: str) -> str:
        return f"[{'x' if self.toggles.get(key, False) else ' '}] {text}"

    def compose(self) -> ComposeResult:
        yield Static("Monitor columns", classes="section-title")
        for group_name, options in self.grouped_options:
            yield Static(group_name, classes="monitor-fields-group-title")
            for key, label in options:
                safe_key = key.replace(".", "-")
                self.toggles[key] = key in self.selected
                self.labels[key] = label
                button_id = f"monitor-field-{safe_key}"
                self.button_field_map[button_id] = key
                yield Button(
                    self._label(key, label),
                    id=button_id,
                    classes="monitor-field-toggle",
                )
        yield Button("Save Monitor Fields", variant="primary", id="save-monitor-fields")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "save-monitor-fields":
            fields = [key for key, enabled in self.toggles.items() if enabled]
            self.post_message(self.Submitted(fields))
            return
        if not button_id.startswith("monitor-field-"):
            return
        field_key = self.button_field_map.get(button_id)
        if field_key is None or field_key not in self.toggles:
            return
        self.toggles[field_key] = not self.toggles[field_key]
        event.button.label = self._label(field_key, self.labels.get(field_key, field_key))


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


__all__ = ["EndpointRow", "EndpointForm", "MonitorFieldsForm"]
