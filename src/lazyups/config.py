"""Configuration management for LazyUPS."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List

from .models import Endpoint

CONFIG_FILENAME = ".lazynuts.config"
DEFAULT_CONFIG_PATH = Path.home() / CONFIG_FILENAME


class ConfigManager:
    """Reads and writes LazyUPS configuration."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else DEFAULT_CONFIG_PATH

    def load_endpoints(self) -> List[Endpoint]:
        """Load configured endpoints."""

        if not self.path.exists():
            return []

        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return []

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

        payload = {
            "endpoints": [asdict(endpoint) for endpoint in endpoints],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2))


__all__ = ["ConfigManager", "CONFIG_FILENAME", "DEFAULT_CONFIG_PATH"]
