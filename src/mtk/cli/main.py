"""Root CLI application for mtk."""

import typer

from mtk import __version__
from mtk.cli import analyze, apk, device

app = typer.Typer(
    name="mtk",
    help=(
        "mtk - a multi-platform mobile pentesting toolkit "
        "(Android available now; iOS/IPA and device management on the roadmap)."
    ),
    no_args_is_help=True,
)

# Register subcommands
app.add_typer(analyze.app, name="analyze", help="Static APK analysis utilities")
app.add_typer(device.app, name="device", help="Manage connected Android devices")
app.add_typer(apk.app, name="apk", help="Pull and manage APK files")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"mtk {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """mtk - a multi-platform mobile pentesting toolkit."""
    pass


if __name__ == "__main__":
    app()
