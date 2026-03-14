"""Command-line interface for LazyUPS."""

from __future__ import annotations

from pathlib import Path

import click

from .app import VALID_SCREENS, LazyUPSApp
from .config import ConfigManager, resolve_config_path
from .version import __version__


@click.command()
@click.version_option(version=__version__, prog_name="lazyups")
@click.option(
    "--screen",
    type=click.Choice(VALID_SCREENS),
    default="monitor",
    show_default=True,
    help="Start the application on the specified screen.",
)
@click.option(
    "--config-file",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help=(
        "Use a specific config file path. "
        "Default search order: ~/.lazyups.config, /etc/lazyups.config, /usr/local/etc/lazyups.config."
    ),
)
def main(screen: str, config_file: Path | None) -> None:
    """Run the LazyUPS Textual interface."""

    config = ConfigManager(resolve_config_path(config_file))
    valid, error = config.validate_startup_file()
    if not valid and error is not None:
        raise click.ClickException(error)

    app = LazyUPSApp(config=config, start_screen=screen)
    app.run()


if __name__ == "__main__":
    main()
