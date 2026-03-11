"""Simple in-memory store for LazyUPS."""

from __future__ import annotations

from typing import Iterable, List

from .models import Endpoint


class EndpointsStore:
    """Stores configured endpoints."""

    def __init__(self, endpoints: Iterable[Endpoint] | None = None) -> None:
        self._endpoints: List[Endpoint] = list(endpoints or [])

    def list(self) -> List[Endpoint]:
        return list(self._endpoints)

    def add(self, endpoint: Endpoint) -> None:
        if endpoint not in self._endpoints:
            self._endpoints.append(endpoint)

    def remove(self, endpoint: Endpoint) -> None:
        self._endpoints = [item for item in self._endpoints if item != endpoint]

    def replace(self, endpoints: Iterable[Endpoint]) -> None:
        self._endpoints = list(endpoints)

    def update(self, previous: Endpoint, new_endpoint: Endpoint) -> None:
        for index, item in enumerate(self._endpoints):
            if item == previous:
                self._endpoints[index] = new_endpoint
                return
        # If the previous entry is missing, fall back to adding
        self.add(new_endpoint)


__all__ = ["EndpointsStore"]
