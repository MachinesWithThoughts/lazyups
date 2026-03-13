"""Textual application for LazyUPS."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import nut2
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.events import Click
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, ListItem, ListView, Static

from .config import ConfigManager, DEFAULT_MONITOR_FIELDS
from .models import Endpoint
from .store import EndpointsStore
from .widgets import EndpointForm, EndpointRow
from .version import __version__

VALID_SCREENS = ("monitor", "details", "devices", "fields", "settings")
SCREEN_TO_MENU_INDEX = {"monitor": 0, "details": 1, "devices": 3, "fields": 4, "settings": 3}
BASE_MONITOR_FIELDS: list[str] = [
    "model",
    "battery.charge",
    "battery.runtime",
    "battery.voltage",
    "input.voltage",
    "ups.beeper.status",
    "ups.load",
    "ups.status",
]


def discover_available_fields(store: EndpointsStore) -> list[str]:
    fields = set(BASE_MONITOR_FIELDS)
    for endpoint in store.list():
        endpoint_devices, _ = fetch_endpoint_devices(endpoint)
        for device in endpoint_devices:
            fields.update(device.values.keys())
    return sorted(fields)


def append_jsonl_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def grouped_field_sections(fields: list[str]) -> list[tuple[str, list[str]]]:
    groups: dict[str, list[str]] = {
        "Device": [],
        "Battery": [],
        "Input": [],
        "UPS": [],
        "Output": [],
        "Other": [],
    }
    for field in fields:
        if field == "model" or field.startswith("device."):
            groups["Device"].append(field)
        elif field.startswith("battery."):
            groups["Battery"].append(field)
        elif field.startswith("input."):
            groups["Input"].append(field)
        elif field.startswith("ups."):
            groups["UPS"].append(field)
        elif field.startswith("output."):
            groups["Output"].append(field)
        else:
            groups["Other"].append(field)

    grouped: list[tuple[str, list[str]]] = []
    for name in ("Device", "Battery", "Input", "UPS", "Output", "Other"):
        section_fields = sorted(set(groups[name]))
        if section_fields:
            grouped.append((name, section_fields))
    return grouped


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
            ListItem(Static("Settings", id="menu-settings-heading")),
            ListItem(Static("- Devices", id="menu-devices")),
            ListItem(Static("- Fields", id="menu-fields")),
        )

    def compose(self) -> ComposeResult:
        yield self.list_view


class MonitorScreen(Static):
    """Continuously poll UPS devices and show a fleet status table."""

    poll_interval = reactive(5)

    BINDINGS = [
        ("space", "refresh_now", "Refresh now"),
        ("s", "save_settings", "Save"),
    ]

    def __init__(self, store: EndpointsStore, config: ConfigManager, **kwargs) -> None:
        super().__init__(**kwargs)
        self.store = store
        self.config = config
        self.monitor_log_path = Path.cwd() / "LazyUPS-monitoring.jsonl"
        self.continuous_save_enabled = False

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Polling UPS devices...", id="monitor-status"),
            DataTable(id="monitor-table"),
            classes="monitor-container",
        )

    @staticmethod
    def _get_value(values: dict[str, str], key: str, fallback: str = "-") -> str:
        value = values.get(key)
        if value is None or value == "":
            return fallback
        return value

    @classmethod
    def build_row_values(cls, device: DeviceSnapshot) -> dict[str, str]:
        values = {key: str(value) for key, value in device.values.items()}
        values["model"] = cls._get_value(values, "device.model", cls._get_value(values, "ups.model"))
        return values

    def selected_fields(self) -> list[str]:
        selected = self.config.load_monitor_fields()
        return selected or list(DEFAULT_MONITOR_FIELDS)

    def rebuild_columns(self) -> None:
        table = self.query_one("#monitor-table", DataTable)
        table.clear(columns=True)
        fields = self.selected_fields()
        table.add_columns("Device", *fields)

    def refresh_monitor(self) -> None:
        table = self.query_one("#monitor-table", DataTable)
        status = self.query_one("#monitor-status", Static)
        fields = self.selected_fields()

        # Rebuild each refresh so monitor column selection changes apply immediately.
        self.rebuild_columns()
        table = self.query_one("#monitor-table", DataTable)

        errors: list[str] = []
        row_count = 0
        captured_at = datetime.now()
        snapshot_rows: list[dict[str, object]] = []

        for endpoint in self.store.list():
            endpoint_devices, endpoint_errors = fetch_endpoint_devices(endpoint)
            errors.extend(endpoint_errors)
            for device in endpoint_devices:
                values = self.build_row_values(device)
                table.add_row(device.upsc_target(), *(values.get(field, "-") for field in fields))
                row_count += 1
                snapshot_rows.append(
                    {
                        "captured_at": captured_at.isoformat(),
                        "target": device.upsc_target(),
                        "endpoint": {
                            "name": endpoint.name,
                            "host": endpoint.host,
                            "port": endpoint.port,
                        },
                        "description": device.description,
                        "monitor_values": {field: values.get(field, "-") for field in fields},
                    }
                )

        if row_count == 0:
            if errors:
                status.update("Polling failed: " + " | ".join(errors))
            else:
                status.update("No devices found. Add endpoints in Settings.")
            return

        if self.continuous_save_enabled:
            append_jsonl_rows(self.monitor_log_path, snapshot_rows)

        updated_at = captured_at.strftime("%Y-%m-%d %H:%M:%S")
        saved_suffix = " (saved)" if self.continuous_save_enabled else ""
        if errors:
            status.update(
                f"Showing {row_count} device(s) with {len(errors)} error(s). "
                f"Refresh every {self.poll_interval}s · updated {updated_at}{saved_suffix}"
            )
        else:
            status.update(
                f"Showing {row_count} device(s). Refresh every {self.poll_interval}s · updated {updated_at}{saved_suffix}"
            )

    def action_refresh_now(self) -> None:
        self.refresh_monitor()

    def action_save_settings(self) -> None:
        self.continuous_save_enabled = not self.continuous_save_enabled
        state = "enabled" if self.continuous_save_enabled else "disabled"
        self.query_one("#monitor-status", Static).update(
            f"Auto-save {state} (writes refresh snapshots to {self.monitor_log_path})"
        )
        self.refresh_monitor()

    def on_mount(self) -> None:
        table = self.query_one("#monitor-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        self.rebuild_columns()
        self.refresh_monitor()
        self.set_interval(self.poll_interval, self.refresh_monitor)


class DetailsScreen(Static):
    """Details view for querying `upsc name@host` data."""

    poll_interval = reactive(5)

    BINDINGS = [
        ("s", "save_details", "Save"),
        ("space", "refresh_now", "Refresh now"),
    ]

    def __init__(self, store: EndpointsStore, config: ConfigManager, **kwargs) -> None:
        super().__init__(**kwargs)
        self.store = store
        self.config = config
        self.devices: list[DeviceSnapshot] = []
        self.selected_index = 0
        self.details_log_path = Path.cwd() / "LazyUPS-details.jsonl"

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Polling UPS devices...", id="details-status"),
            Horizontal(
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
            ),
        )

    @staticmethod
    def format_device_details(device: DeviceSnapshot, highlighted_fields: set[str] | None = None) -> str:
        highlight = highlighted_fields or set()
        lines = [
            f"upsc {device.upsc_target()}",
            f"Endpoint: {device.endpoint.label()} ({device.endpoint.host}:{device.endpoint.port})",
            f"Description: {device.description or '(none)'}",
            "",
        ]
        for key, value in device.values.items():
            if key in highlight:
                lines.append(f"[green]{key}[/green]: {value}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines).rstrip()

    @staticmethod
    def format_errors(errors: list[str]) -> str:
        if not errors:
            return "No endpoints configured yet. Add one in Settings."
        return "Unable to load device details:\n\n" + "\n".join(f"- {item}" for item in errors)

    @staticmethod
    def format_status(row_count: int, error_count: int, poll_interval: int, updated_at: str) -> str:
        if error_count:
            return (
                f"Showing {row_count} device(s) with {error_count} error(s). "
                f"Refresh every {poll_interval}s · updated {updated_at}"
            )
        return f"Showing {row_count} device(s). Refresh every {poll_interval}s · updated {updated_at}"

    def refresh_details(self) -> None:
        list_view = self.query_one("#details-device-list", ListView)
        output = self.query_one("#details-output-text", Static)
        status = self.query_one("#details-status", Static)

        list_view.remove_children()
        previous_selected_index = self.selected_index
        self.devices = []
        errors: list[str] = []
        captured_at = datetime.now()

        for endpoint in self.store.list():
            endpoint_devices, endpoint_errors = fetch_endpoint_devices(endpoint)
            self.devices.extend(endpoint_devices)
            errors.extend(endpoint_errors)

        for index, device in enumerate(self.devices):
            list_view.mount(ListItem(Static(f"• {device.menu_label()}", id=f"details-device-{index}")))

        sidebar = self.query_one(".details-sidebar", Vertical)
        if self.devices:
            longest_label = max(len(f"• {device.menu_label()}") for device in self.devices)
            sidebar.styles.width = max(24, min(60, longest_label + 2))
        else:
            sidebar.styles.width = 24

        selected_fields = set(self.config.load_monitor_fields())
        if self.devices:
            self.selected_index = max(0, min(previous_selected_index, len(self.devices) - 1))
            output.update(self.format_device_details(self.devices[self.selected_index], selected_fields))
            list_view.index = self.selected_index
        else:
            self.selected_index = 0
            output.update(self.format_errors(errors))

        updated_at = captured_at.strftime("%Y-%m-%d %H:%M:%S")
        row_count = len(self.devices)
        if row_count == 0:
            if errors:
                status.update("Polling failed: " + " | ".join(errors))
            else:
                status.update("No devices found. Add endpoints in Settings.")
            return

        status.update(self.format_status(row_count, len(errors), self.poll_interval, updated_at))

    def action_refresh_now(self) -> None:
        self.refresh_details()

    def action_save_details(self) -> None:
        output = self.query_one("#details-output-text", Static)
        if not self.devices:
            output.update("Save skipped: no device selected")
            return

        self.selected_index = max(0, min(self.selected_index, len(self.devices) - 1))
        device = self.devices[self.selected_index]
        row = {
            "captured_at": datetime.now().isoformat(),
            "target": device.upsc_target(),
            "endpoint": {
                "name": device.endpoint.name,
                "host": device.endpoint.host,
                "port": device.endpoint.port,
            },
            "description": device.description,
            "values": {key: str(value) for key, value in device.values.items()},
        }
        append_jsonl_rows(self.details_log_path, [row])
        selected_fields = set(self.config.load_monitor_fields())
        output.update(self.format_device_details(device, selected_fields) + "\n\n[green]Saved[/green]")

    def on_mount(self) -> None:
        self.refresh_details()
        self.set_interval(self.poll_interval, self.refresh_details)

    def on_list_view_selected(self, event: ListView.Selected) -> None:  # type: ignore[override]
        if event.list_view.id != "details-device-list":
            return
        event.stop()
        widget_id = event.item.query_one(Static).id or ""
        if not widget_id.startswith("details-device-"):
            return
        index = int(widget_id.removeprefix("details-device-"))
        if 0 <= index < len(self.devices):
            self.selected_index = index
            selected_fields = set(self.config.load_monitor_fields())
            self.query_one("#details-output-text", Static).update(
                self.format_device_details(self.devices[self.selected_index], selected_fields)
            )


class DevicesScreen(Static):
    """Settings sub-screen for managing NUT endpoints."""

    def __init__(self, store: EndpointsStore, config: ConfigManager, **kwargs) -> None:
        super().__init__(**kwargs)
        self.store = store
        self.config = config
        self.form: EndpointForm | None = None

    def compose(self) -> ComposeResult:
        self.form = EndpointForm(classes="endpoint-form")
        yield VerticalScroll(
            Vertical(
                Static("Configured endpoints", classes="section-title"),
                Container(id="endpoint-list", classes="endpoint-list"),
                self.form,
                classes="settings-container",
            ),
            id="settings-scroll-devices",
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


class DisplayFieldsScreen(Static):
    """Settings sub-screen showing all available monitor fields."""

    def __init__(self, store: EndpointsStore, **kwargs) -> None:
        super().__init__(**kwargs)
        self.store = store
        self.field_widget_map: dict[str, str] = {}
        self._field_render_token = 0

    BINDINGS = [
        ("up", "scroll_up", "Up"),
        ("down", "scroll_down", "Down"),
        ("pageup", "page_up", "Page Up"),
        ("pagedown", "page_down", "Page Down"),
        ("home", "scroll_home", "Top"),
        ("end", "scroll_end", "Bottom"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            VerticalScroll(
                id="settings-scroll-fields",
                can_focus=True,
            ),
            Static("Tip: click a field to toggle whether it displays on Monitor/Details.", id="fields-tip"),
        )

    def on_mount(self) -> None:
        self.refresh_fields_form()
        self.focus_scroller()

    def on_show(self) -> None:
        self.focus_scroller()

    def focus_scroller(self) -> None:
        self.query_one("#settings-scroll-fields", VerticalScroll).focus()

    def _scroller(self) -> VerticalScroll:
        return self.query_one("#settings-scroll-fields", VerticalScroll)

    def action_scroll_up(self) -> None:
        self._scroller().scroll_up()

    def action_scroll_down(self) -> None:
        self._scroller().scroll_down()

    def action_page_up(self) -> None:
        self._scroller().scroll_page_up()

    def action_page_down(self) -> None:
        self._scroller().scroll_page_down()

    def action_scroll_home(self) -> None:
        self._scroller().scroll_home(animate=False)

    def action_scroll_end(self) -> None:
        self._scroller().scroll_end(animate=False)

    def _save_toggled_field(self, field: str) -> None:
        current_fields = self.app.config.load_monitor_fields()
        if field in current_fields:
            updated_fields = [item for item in current_fields if item != field]
        else:
            updated_fields = [*current_fields, field]

        self.app.config.save_monitor_fields(updated_fields)
        self.refresh_fields_form()

        monitor_screen = self.app.query_one("#monitor", MonitorScreen)
        monitor_screen.refresh_monitor()

    def on_click(self, event: Click) -> None:
        widget_id = event.widget.id or ""
        field = self.field_widget_map.get(widget_id)
        if field is None:
            return
        event.stop()
        self._save_toggled_field(field)

    def refresh_fields_form(self) -> None:
        scroller = self.query_one("#settings-scroll-fields", VerticalScroll)
        scroller.remove_children()
        self.field_widget_map.clear()
        self._field_render_token += 1

        fields = discover_available_fields(self.store)
        sections = grouped_field_sections(fields)
        selected = set(self.app.config.load_monitor_fields())

        if not sections:
            scroller.mount(Static("No fields discovered yet. Add a device in Settings > Devices."))
            return

        scroller.mount(Static("Available fields (deduplicated)"))
        scroller.mount(Static(""))

        field_index = 0
        for section_name, section_fields in sections:
            scroller.mount(Static(section_name))
            for field in section_fields:
                widget_id = f"display-field-{self._field_render_token}-{field_index}"
                field_index += 1
                self.field_widget_map[widget_id] = field
                if field in selected:
                    scroller.mount(Static(f"  [green]{field}[/green]", id=widget_id, classes="monitor-field-line"))
                else:
                    scroller.mount(Static(f"  {field}", id=widget_id, classes="monitor-field-line"))
            scroller.mount(Static(""))



class LazyUPSApp(App):
    """Main Textual application."""

    TITLE = "LazyUPS"
    CSS_PATH = "app.css"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
        ("space", "refresh_now", "[space] refresh"),
        ("s", "save_settings", "[s]ave"),
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
                self.monitor_screen = MonitorScreen(self.store, self.config, id="monitor")
                self.details_screen = DetailsScreen(self.store, self.config, id="details")
                self.devices_screen = DevicesScreen(self.store, self.config, id="devices")
                self.display_fields_screen = DisplayFieldsScreen(self.store, id="fields")
                yield self.monitor_screen
                yield self.details_screen
                yield self.devices_screen
                yield self.display_fields_screen
        yield Footer()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in {"refresh_now", "save_settings"}:
            return self.monitor_screen.display or self.details_screen.display
        return None

    def action_quit(self) -> None:
        self.exit()

    def on_key(self, event: events.Key) -> None:
        if event.key in {"q", "escape", "ctrl+q", "ctrl+c"}:
            event.stop()
            self.exit()

    def action_refresh_now(self) -> None:
        if self.monitor_screen.display:
            self.monitor_screen.action_refresh_now()
        elif self.details_screen.display:
            self.details_screen.action_refresh_now()

    def action_save_settings(self) -> None:
        if self.monitor_screen.display:
            self.monitor_screen.action_save_settings()
        elif self.details_screen.display:
            self.details_screen.action_save_details()

    def on_mount(self) -> None:
        self.show_screen(self.start_screen)

    def show_screen(self, screen_id: str) -> None:
        if screen_id == "settings":
            screen_id = "devices"
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
            self.query_one("#monitor", MonitorScreen).refresh_monitor()
        elif widget_id == "menu-details":
            self.show_screen("details")
            self.query_one("#details", DetailsScreen).refresh_details()
        elif widget_id == "menu-settings-heading":
            self.show_screen("devices")
            self.query_one("#devices", DevicesScreen).refresh_endpoints()
        elif widget_id == "menu-devices":
            self.show_screen("devices")
            self.query_one("#devices", DevicesScreen).refresh_endpoints()
        elif widget_id == "menu-fields":
            self.show_screen("fields")
            fields_screen = self.query_one("#fields", DisplayFieldsScreen)
            fields_screen.refresh_fields_form()
            fields_screen.focus_scroller()


__all__ = [
    "DeviceSnapshot",
    "LazyUPSApp",
    "VALID_SCREENS",
    "fetch_endpoint_devices",
]
