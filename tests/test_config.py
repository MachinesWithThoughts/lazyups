"""Tests for configuration management."""

from __future__ import annotations

from pathlib import Path

from lazyups.config import DEFAULT_MONITOR_FIELDS, ConfigManager
from lazyups.models import Endpoint


def test_config_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / ".lazyups.config"
    manager = ConfigManager(config_path)

    endpoints = [Endpoint("ups1", 3493, "UPS 1"), Endpoint("ups2", 4000, None)]
    manager.save_endpoints(endpoints)

    loaded = manager.load_endpoints()
    assert loaded == endpoints


def test_config_handles_missing_file(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / "missing.json")
    assert manager.load_endpoints() == []
    assert manager.load_monitor_fields() == DEFAULT_MONITOR_FIELDS


def test_monitor_fields_round_trip(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / ".lazyups.config")

    manager.save_monitor_fields(["battery.charge", "ups.status"])

    loaded = manager.load_monitor_fields()
    assert loaded == ["battery.charge", "ups.status"]


def test_save_endpoints_preserves_monitor_fields(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / ".lazyups.config")
    manager.save_monitor_fields(["ups.status"])

    manager.save_endpoints([Endpoint("ups1", 3493, "UPS 1")])

    assert manager.load_monitor_fields() == ["ups.status"]


def test_validate_startup_file_rejects_invalid_json(tmp_path: Path) -> None:
    config_path = tmp_path / ".lazyups.config"
    config_path.write_text("{not json")
    manager = ConfigManager(config_path)

    valid, error = manager.validate_startup_file()
    assert valid is False
    assert error is not None


def test_validate_startup_file_accepts_valid_shape(tmp_path: Path) -> None:
    config_path = tmp_path / ".lazyups.config"
    config_path.write_text('{"endpoints": [{"host": "ups1", "port": 3493}], "monitor_fields": ["ups.status"]}')
    manager = ConfigManager(config_path)

    valid, error = manager.validate_startup_file()
    assert valid is True
    assert error is None
