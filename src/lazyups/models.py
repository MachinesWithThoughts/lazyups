"""Data models for LazyUPS."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Endpoint:
    """Represents a NUT endpoint."""

    host: str
    port: int = 3493
    name: str | None = None

    def label(self) -> str:
        return f"{self.host}:{self.port}"


__all__ = ["Endpoint"]
