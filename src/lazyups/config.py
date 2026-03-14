"""Configuration management for LazyUPS."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List

from .models import Endpoint

CONFIG_FILENAME = ".lazyups.config"
DEFAULT_CONFIG_PATH = Path.home() / CONFIG_FILENAME
SYSTEM_CONFIG_PATHS = [
    Path("/etc/lazyups.config"),
    Path("/usr/local/etc/lazyups.config"),
]

DEFAULT_MONITOR_FIELDS = [
    "battery.charge",
    "battery.runtime",
    "battery.voltage",
    "model",
    "input.voltage",
    "ups.beeper.status",
    "ups.load",
    "ups.status",
]


def resolve_config_path(explicit_path: Path | None = None) -> Path:
    """Resolve config path from explicit flag or fallback search order."""

    if explicit_path is not None:
        return explicit_path.expanduser()

    candidates = [DEFAULT_CONFIG_PATH, *SYSTEM_CONFIG_PATHS]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return DEFAULT_CONFIG_PATH


class ConfigManager:
    """Reads and writes LazyUPS configuration."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else DEFAULT_CONFIG_PATH

    def validate_startup_file(self) -> tuple[bool, str | None]:
        """Validate the config file shape before app startup."""

        if not self.path.exists():
            return True, None

        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError as exc:
            return False, f"Invalid JSON in {self.path}: {exc}"

        if not isinstance(data, dict):
            return False, f"Invalid config in {self.path}: top-level object must be a JSON object"

        endpoints = data.get("endpoints")
        if endpoints is not None and not isinstance(endpoints, list):
            return False, f"Invalid config in {self.path}: 'endpoints' must be a list"

        if isinstance(endpoints, list):
            for index, item in enumerate(endpoints):
                if not isinstance(item, dict):
                    return False, f"Invalid config in {self.path}: endpoints[{index}] must be an object"
                host = item.get("host")
                if host is not None and not isinstance(host, str):
                    return False, f"Invalid config in {self.path}: endpoints[{index}].host must be a string"
                port = item.get("port", 3493)
                try:
                    port_int = int(port)
                except (TypeError, ValueError):
                    return False, f"Invalid config in {self.path}: endpoints[{index}].port must be an integer"
                if not (1 <= port_int <= 65535):
                    return False, f"Invalid config in {self.path}: endpoints[{index}].port out of range"

        monitor_fields = data.get("monitor_fields")
        if monitor_fields is not None:
            if not isinstance(monitor_fields, list) or any(not isinstance(item, str) for item in monitor_fields):
                return False, f"Invalid config in {self.path}: 'monitor_fields' must be a list of strings"

        return True, None

    def _load_raw(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return data

    def _save_raw(self, payload: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2))

    def load_endpoints(self) -> List[Endpoint]:
        """Load configured endpoints."""

        data = self._load_raw()

        endpoints: List[Endpoint] = []
        for item in data.get("endpoints", []):
            host = item.get("host")
            port = item.get("port", 3493)
            name = item.get("name")
            if not host:
                continue
            try:
                port_int = int(port)
            except (TypeError, ValueError):
                continue
            endpoints.append(Endpoint(host=host, port=port_int, name=name or None))
        return endpoints

    def save_endpoints(self, endpoints: Iterable[Endpoint]) -> None:
        """Persist endpoints to disk."""

        payload = self._load_raw()
        payload["endpoints"] = [asdict(endpoint) for endpoint in endpoints]
        self._save_raw(payload)

    def load_monitor_fields(self) -> list[str]:
        """Load selected monitor fields."""

        data = self._load_raw()
        fields = data.get("monitor_fields")
        if not isinstance(fields, list):
            return list(DEFAULT_MONITOR_FIELDS)
        normalized = [str(item) for item in fields if isinstance(item, str)]
        return normalized or list(DEFAULT_MONITOR_FIELDS)

    def save_monitor_fields(self, fields: list[str]) -> None:
        """Persist selected monitor fields."""

        payload = self._load_raw()
        payload["monitor_fields"] = list(fields)
        self._save_raw(payload)


__all__ = [
    "ConfigManager",
    "CONFIG_FILENAME",
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_MONITOR_FIELDS",
    "SYSTEM_CONFIG_PATHS",
    "resolve_config_path",
]
