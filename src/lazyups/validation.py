"""Validation helpers for LazyUPS."""

from __future__ import annotations

import importlib
import sys
from typing import Sequence

from .app import VALID_SCREENS, LazyUPSApp

REQUIRED_MODULES = [
    "lazyups",
    "lazyups.app",
    "lazyups.config",
    "lazyups.store",
    "lazyups.widgets",
    "textual",
    "click",
    "rich",
]


def validate_runtime() -> None:
    """Ensure that required Python modules can be imported."""

    missing: list[str] = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - pragma ensures full report if raised
            missing.append(f"{module}: {exc}")
    if missing:
        message = "Runtime validation failed:\n" + "\n".join(f"  - {item}" for item in missing)
        raise RuntimeError(message)


class ScreenValidationApp(LazyUPSApp):
    """LazyUPS application variant that cycles through screens for validation."""

    def __init__(self, *, screens: Sequence[str], delay: float) -> None:
        super().__init__()
        if not screens:
            raise ValueError("At least one screen id must be provided")
        self._screen_sequence = list(screens)
        self._delay = delay
        self._cursor = 0

    def on_mount(self) -> None:
        super().on_mount()
        self.call_after_refresh(self._advance)

    def _advance(self) -> None:
        if self._cursor >= len(self._screen_sequence):
            self.exit(None)
            return
        screen_id = self._screen_sequence[self._cursor]
        if screen_id not in VALID_SCREENS:
            self.exit(ValueError(f"Unknown screen id '{screen_id}'"))
            return

        resolved_screen_id = "devices" if screen_id == "settings" else screen_id
        self.show_screen(screen_id)
        widget = self.query_one(f"#{resolved_screen_id}")
        widget.refresh()
        self._cursor += 1
        self.set_timer(self._delay, self._advance)


def validate_screens(*, screens: Sequence[str] | None = None, delay: float = 2.0) -> None:
    """Cycle through the requested screens to ensure they render without errors."""

    sequence = list(screens) if screens else ["monitor", "details", "settings"]
    app = ScreenValidationApp(screens=sequence, delay=delay)
    app.run(headless=True, size=(80, 24))


def _cli(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="lazyups.validation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("runtime", help="validate runtime module imports")

    screens_parser = subparsers.add_parser("screens", help="validate screens render correctly")
    screens_parser.add_argument("screens", nargs="*", help="screen ids to validate in order")
    screens_parser.add_argument("--delay", type=float, default=2.0, help="seconds to wait per screen")

    args = parser.parse_args(argv)

    if args.command == "runtime":
        validate_runtime()
    elif args.command == "screens":
        validate_screens(screens=args.screens, delay=args.delay)
    else:  # pragma: no cover
        parser.error(f"Unexpected command {args.command}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli())
