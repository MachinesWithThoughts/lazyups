"""Package version information."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _resolve_version() -> str:
    """Return installed package version, with local fallback for dev runs."""

    try:
        return version("lazyups")
    except PackageNotFoundError:
        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        if pyproject.exists():
            for line in pyproject.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("version") and "=" in line:
                    return line.split("=", 1)[1].strip().strip('"')
        return "0.0.0"


__version__ = _resolve_version()

__all__ = ["__version__"]
