"""Smoke tests for LazyUPS Textual app."""

from __future__ import annotations

from lazyups.app import DetailsScreen, DeviceSnapshot, LazyUPSApp, MonitorScreen
from lazyups.models import Endpoint
from lazyups.store import EndpointsStore


def test_endpoints_store_roundtrip() -> None:
    store = EndpointsStore()
    endpoint = Endpoint("ups.example.com", 3493, "Example UPS")

    store.add(endpoint)
    assert store.list() == [endpoint]

    store.remove(endpoint)
    assert store.list() == []


def test_endpoint_label_prefers_friendly_name() -> None:
    endpoint = Endpoint("ups.example.com", 3493, "Rack UPS")
    assert endpoint.label() == "Rack UPS"


def test_endpoint_label_falls_back_to_host_port() -> None:
    endpoint = Endpoint("ups.example.com", 3493, None)
    assert endpoint.label() == "ups.example.com:3493"


def test_details_screen_shows_empty_state() -> None:
    assert DetailsScreen.format_errors([]) == "No endpoints configured yet. Add one in Settings."


def test_details_screen_status_without_errors() -> None:
    status = DetailsScreen.format_status(2, 0, 5, "2026-03-12 19:20:00")
    assert status == "Showing 2 device(s). Refresh every 5s · updated 2026-03-12 19:20:00"


def test_details_screen_status_with_errors() -> None:
    status = DetailsScreen.format_status(2, 1, 5, "2026-03-12 19:20:00")
    assert status == "Showing 2 device(s) with 1 error(s). Refresh every 5s · updated 2026-03-12 19:20:00"


def test_details_screen_renders_upsc_device_details() -> None:
    endpoint = Endpoint("ups.example.com", 3493, "Rack UPS")
    device = DeviceSnapshot(
        endpoint=endpoint,
        ups_name="ups",
        description="Main Rack UPS",
        values={"battery.charge": "100", "ups.status": "OL"},
    )

    rendered = DetailsScreen.format_device_details(device, {"battery.charge"})
    assert "upsc ups@ups.example.com" in rendered
    assert "Endpoint: Rack UPS (ups.example.com:3493)" in rendered
    assert "[green]battery.charge[/green]: 100" in rendered
    assert "ups.status: OL" in rendered


def test_monitor_row_contains_requested_fields() -> None:
    endpoint = Endpoint("ups.example.com", 3493, "Rack UPS")
    device = DeviceSnapshot(
        endpoint=endpoint,
        ups_name="myups",
        description="Main",
        values={
            "battery.charge": "98",
            "battery.runtime": "3600",
            "battery.voltage": "13.5",
            "device.model": "Smart-UPS 1500",
            "input.voltage": "120.0",
            "ups.beeper.status": "enabled",
            "ups.load": "15",
            "ups.status": "OL",
        },
    )

    row = MonitorScreen.build_row_values(device)
    assert row["battery.charge"] == "98"
    assert row["battery.runtime"] == "3600"
    assert row["battery.voltage"] == "13.5"
    assert row["model"] == "Smart-UPS 1500"
    assert row["input.voltage"] == "120.0"
    assert row["ups.beeper.status"] == "enabled"
    assert row["ups.load"] == "15"
    assert row["ups.status"] == "OL"


def test_app_can_instantiate() -> None:
    app = LazyUPSApp()
    assert app is not None
