"""Textual application for LazyUPS."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, ListItem, ListView, Static

from .config import ConfigManager
from .store import EndpointsStore
from .widgets import EndpointForm, EndpointRow
from .version import __version__

VALID_SCREENS = ("monitor", "details", "settings")


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
    """Placeholder for details view."""

    def render(self) -> str:
        return "Details view"


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
                self.details_screen = DetailsScreen(id="details")
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

    def on_list_view_selected(self, event: ListView.Selected) -> None:  # type: ignore[override]
        widget_id = event.item.query_one(Static).id
        if widget_id == "menu-monitor":
            self.show_screen("monitor")
        elif widget_id == "menu-details":
            self.show_screen("details")
            self.query_one("#details", DetailsScreen).refresh()
        elif widget_id == "menu-settings":
            self.show_screen("settings")
            self.query_one("#settings", SettingsScreen).refresh_endpoints()


__all__ = [
    "LazyUPSApp",
    "VALID_SCREENS",
]
