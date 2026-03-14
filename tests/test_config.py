"""Tests for configuration management."""

from __future__ import annotations

from pathlib import Path

from lazyups.config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MONITOR_FIELDS,
    SYSTEM_CONFIG_PATHS,
    ConfigManager,
    resolve_config_path,
)
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


def test_resolve_config_path_uses_explicit_path(tmp_path: Path) -> None:
    explicit = tmp_path / "custom.json"
    assert resolve_config_path(explicit) == explicit


def test_resolve_config_path_uses_default_when_present(monkeypatch, tmp_path: Path) -> None:
    default_path = tmp_path / ".lazyups.config"
    default_path.write_text("{}")
    monkeypatch.setattr("lazyups.config.DEFAULT_CONFIG_PATH", default_path)
    monkeypatch.setattr("lazyups.config.SYSTEM_CONFIG_PATHS", [])

    assert resolve_config_path() == default_path


def test_resolve_config_path_uses_system_fallback(monkeypatch, tmp_path: Path) -> None:
    default_path = tmp_path / ".lazyups.config"
    system_path = tmp_path / "etc-lazyups.config"
    system_path.write_text("{}")

    monkeypatch.setattr("lazyups.config.DEFAULT_CONFIG_PATH", default_path)
    monkeypatch.setattr("lazyups.config.SYSTEM_CONFIG_PATHS", [system_path])

    assert resolve_config_path() == system_path


def test_resolve_config_path_falls_back_to_default(monkeypatch, tmp_path: Path) -> None:
    default_path = tmp_path / ".lazyups.config"
    system_path = tmp_path / "etc-lazyups.config"

    monkeypatch.setattr("lazyups.config.DEFAULT_CONFIG_PATH", default_path)
    monkeypatch.setattr("lazyups.config.SYSTEM_CONFIG_PATHS", [system_path])

    assert resolve_config_path() == default_path


def test_system_config_paths_are_expected() -> None:
    assert SYSTEM_CONFIG_PATHS == [Path("/etc/lazyups.config"), Path("/usr/local/etc/lazyups.config")]
    assert DEFAULT_CONFIG_PATH.name == ".lazyups.config"
