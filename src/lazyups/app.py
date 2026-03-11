"""Textual application for LazyUPS."""

from __future__ import annotations

from dataclasses import dataclass

import nut2
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, ListItem, ListView, Static

from .config import ConfigManager
from .models import Endpoint
from .store import EndpointsStore
from .widgets import EndpointForm, EndpointRow
from .version import __version__

VALID_SCREENS = ("monitor", "details", "settings")
SCREEN_TO_MENU_INDEX = {"monitor": 0, "details": 1, "settings": 2}


@dataclass(slots=True)
class DeviceSnapshot:
    """Materialized response for one `upsc <name>@<host>` device."""

    endpoint: Endpoint
    ups_name: str
    description: str
    values: dict[str, str]

    def upsc_target(self) -> str:
        return f"{self.ups_name}@{self.endpoint.host}"

    def menu_label(self) -> str:
        return f"{self.ups_name} @ {self.endpoint.host}"


def fetch_endpoint_devices(endpoint: Endpoint) -> tuple[list[DeviceSnapshot], list[str]]:
    """Fetch all UPS devices + variables for one endpoint."""

    devices: list[DeviceSnapshot] = []
    errors: list[str] = []

    try:
        client = nut2.PyNUTClient(host=endpoint.host, port=endpoint.port, timeout=5)
        listed = client.list_ups()
        if not listed:
            errors.append(f"{endpoint.label()}: no UPS devices reported")
            return devices, errors

        for ups_name, description in sorted(listed.items()):
            values = client.list_vars(ups_name)
            devices.append(
                DeviceSnapshot(
                    endpoint=endpoint,
                    ups_name=ups_name,
                    description=description,
                    values=dict(sorted(values.items())),
                )
            )
    except Exception as exc:  # pragma: no cover - depends on network/runtime
        errors.append(f"{endpoint.label()} ({endpoint.host}:{endpoint.port}): {exc}")

    return devices, errors


class Menu(Static):
    """Left-hand navigation menu."""

    def __init__(self) -> None:
        super().__init__()
        self.list_view = ListView(
            ListItem(Static("Monitor", id="menu-monitor")),
            ListItem(Static("Details", id="menu-details")),
            ListItem(Static("Settings", id="menu-settings")),
        )

    def compose(self) -> ComposeResult:
        yield self.list_view


class MonitorScreen(Static):
    """Placeholder for monitor view."""

    poll_interval = reactive(1)

    def render(self) -> str:
        return f"Monitor view (poll interval: {self.poll_interval}s)"


class DetailsScreen(Static):
    """Details view for querying `upsc name@host` data."""

    def __init__(self, store: EndpointsStore, **kwargs) -> None:
        super().__init__(**kwargs)
        self.store = store
        self.devices: list[DeviceSnapshot] = []

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Static("Discovered devices", classes="section-title"),
                ListView(id="details-device-list", classes="details-device-list"),
                classes="details-sidebar",
            ),
            VerticalScroll(
                Static("Loading details...", id="details-output-text"),
                id="details-output",
                classes="details-output",
            ),
            id="details-layout",
        )

    @staticmethod
    def format_device_details(device: DeviceSnapshot) -> str:
        lines = [
            f"upsc {device.upsc_target()}",
            f"Endpoint: {device.endpoint.label()} ({device.endpoint.host}:{device.endpoint.port})",
            f"Description: {device.description or '(none)'}",
            "",
        ]
        lines.extend(f"{key}: {value}" for key, value in device.values.items())
        return "\n".join(lines).rstrip()

    @staticmethod
    def format_errors(errors: list[str]) -> str:
        if not errors:
            return "No endpoints configured yet. Add one in Settings."
        return "Unable to load device details:\n\n" + "\n".join(f"- {item}" for item in errors)

    def refresh_details(self) -> None:
        list_view = self.query_one("#details-device-list", ListView)
        output = self.query_one("#details-output-text", Static)

        list_view.remove_children()
        self.devices = []
        errors: list[str] = []

        for endpoint in self.store.list():
            endpoint_devices, endpoint_errors = fetch_endpoint_devices(endpoint)
            self.devices.extend(endpoint_devices)
            errors.extend(endpoint_errors)

        for index, device in enumerate(self.devices):
            list_view.mount(ListItem(Static(device.menu_label(), id=f"details-device-{index}")))

        if self.devices:
            output.update(self.format_device_details(self.devices[0]))
        else:
            output.update(self.format_errors(errors))

    def on_mount(self) -> None:
        self.refresh_details()

    def on_list_view_selected(self, event: ListView.Selected) -> None:  # type: ignore[override]
        if event.list_view.id != "details-device-list":
            return
        event.stop()
        widget_id = event.item.query_one(Static).id or ""
        if not widget_id.startswith("details-device-"):
            return
        index = int(widget_id.removeprefix("details-device-"))
        if 0 <= index < len(self.devices):
            self.query_one("#details-output-text", Static).update(self.format_device_details(self.devices[index]))


class SettingsScreen(Static):
    """Settings view for managing NUT endpoints."""

    def __init__(self, store: EndpointsStore, config: ConfigManager, **kwargs) -> None:
        super().__init__(**kwargs)
        self.store = store
        self.config = config
        self.form: EndpointForm | None = None

    def compose(self) -> ComposeResult:
        self.form = EndpointForm(classes="endpoint-form")
        yield Vertical(
            Static("Configured endpoints", classes="section-title"),
            Container(id="endpoint-list", classes="endpoint-list"),
            self.form,
            classes="settings-container",
        )

    def on_mount(self) -> None:
        self.refresh_endpoints()

    def refresh_endpoints(self) -> None:
        container = self.query_one("#endpoint-list", Container)
        container.remove_children()
        for endpoint in self.store.list():
            container.mount(EndpointRow(endpoint))

    def on_endpoint_form_submitted(self, message: EndpointForm.Submitted) -> None:
        previous = message.previous
        if previous is None:
            self.store.add(message.endpoint)
        else:
            self.store.update(previous, message.endpoint)
        self.config.save_endpoints(self.store.list())
        self.refresh_endpoints()
        if self.form is not None:
            self.form.load_endpoint(None)

    def on_endpoint_row_remove(self, message: EndpointRow.Remove) -> None:
        self.store.remove(message.endpoint)
        self.config.save_endpoints(self.store.list())
        self.refresh_endpoints()
        if self.form is not None and self.form.endpoint == message.endpoint:
            self.form.load_endpoint(None)

    def on_endpoint_row_edit(self, message: EndpointRow.Edit) -> None:
        if self.form is not None:
            self.form.load_endpoint(message.endpoint)


class LazyUPSApp(App):
    """Main Textual application."""

    CSS_PATH = "app.css"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        *,
        store: EndpointsStore | None = None,
        config: ConfigManager | None = None,
        start_screen: str = "monitor",
    ) -> None:
        if start_screen not in VALID_SCREENS:
            raise ValueError(f"Unknown start screen '{start_screen}'. Valid options: {', '.join(VALID_SCREENS)}")
        super().__init__()
        self.config = config or ConfigManager()
        self.store = store or EndpointsStore(self.config.load_endpoints())
        self.start_screen = start_screen

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False, name=f"LazyUPS v{__version__}")
        with Horizontal(id="layout"):
            yield Menu()
            with Container(id="content"):
                self.monitor_screen = MonitorScreen(id="monitor")
                self.details_screen = DetailsScreen(self.store, id="details")
                self.settings_screen = SettingsScreen(self.store, self.config, id="settings")
                yield self.monitor_screen
                yield self.details_screen
                yield self.settings_screen
        yield Footer()

    def on_mount(self) -> None:
        self.show_screen(self.start_screen)

    def show_screen(self, screen_id: str) -> None:
        if screen_id not in VALID_SCREENS:
            raise ValueError(f"Unknown screen '{screen_id}'. Valid options: {', '.join(VALID_SCREENS)}")
        content = self.query_one("#content")
        for widget in content.children:
            widget.display = widget.id == screen_id

        menu = self.query_one(Menu)
        menu.list_view.index = SCREEN_TO_MENU_INDEX[screen_id]

    def on_list_view_selected(self, event: ListView.Selected) -> None:  # type: ignore[override]
        widget_id = event.item.query_one(Static).id
        if widget_id == "menu-monitor":
            self.show_screen("monitor")
        elif widget_id == "menu-details":
            self.show_screen("details")
            self.query_one("#details", DetailsScreen).refresh_details()
        elif widget_id == "menu-settings":
            self.show_screen("settings")
            self.query_one("#settings", SettingsScreen).refresh_endpoints()


__all__ = [
    "DeviceSnapshot",
    "LazyUPSApp",
    "VALID_SCREENS",
    "fetch_endpoint_devices",
]
