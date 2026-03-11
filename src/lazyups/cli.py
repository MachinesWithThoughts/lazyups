"""Command-line interface for LazyUPS."""

from __future__ import annotations

import click

from .app import LazyUPSApp, VALID_SCREENS
from .config import ConfigManager


@click.command()
@click.option(
    "--start-screen",
    type=click.Choice(VALID_SCREENS),
    default="monitor",
    show_default=True,
    help="Start the application on the specified screen.",
)
def main(start_screen: str) -> None:
    """Run the LazyUPS Textual interface."""

    config = ConfigManager()
    valid, error = config.validate_startup_file()
    if not valid and error is not None:
        raise click.ClickException(error)

    app = LazyUPSApp(config=config, start_screen=start_screen)
    app.run()


if __name__ == "__main__":
    main()
