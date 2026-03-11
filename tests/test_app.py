"""Smoke tests for LazyUPS Textual app."""

from __future__ import annotations

from lazyups.app import LazyUPSApp
from lazyups.models import Endpoint
from lazyups.store import EndpointsStore


def test_endpoints_store_roundtrip() -> None:
    store = EndpointsStore()
    endpoint = Endpoint("ups.example.com", 3493, "Example UPS")

    store.add(endpoint)
    assert store.list() == [endpoint]

    store.remove(endpoint)
    assert store.list() == []


def test_app_can_instantiate() -> None:
    app = LazyUPSApp()
    assert app is not None
