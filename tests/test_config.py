"""Tests for configuration management."""

from __future__ import annotations

from pathlib import Path

from lazyups.config import ConfigManager
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
