"""Command-line interface for LazyUPS."""

from __future__ import annotations

import click

from .app import LazyUPSApp, VALID_SCREENS
from .config import ConfigManager
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
def main(screen: str) -> None:
    """Run the LazyUPS Textual interface."""

    config = ConfigManager()
    valid, error = config.validate_startup_file()
    if not valid and error is not None:
        raise click.ClickException(error)

    app = LazyUPSApp(config=config, start_screen=screen)
    app.run()


if __name__ == "__main__":
    main()
