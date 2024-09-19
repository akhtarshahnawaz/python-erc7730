from pathlib import Path
from typing import Annotated

import typer

from rich import print

app = typer.Typer(
    name="erc7730",
    no_args_is_help=True,
    help="""
    ERC-7730 tool.
    """,
)


@app.command(
    name="lint",
    short_help="Validate a descriptor file.",
    help="""
    Validate a descriptor file.
    """,
)
def lint(
    path: Annotated[Path, typer.Argument(help="The file path")],
    demo: Annotated[bool, typer.Option(help="Enable demo mode")] = False,
) -> None:
    from erc7730.linter.lint import lint_all

    outputs = lint_all(path, demo)

    for output in outputs:
        p = output.file.name if output.file is not None else "unknown file"
        print(f"[red]{p}: {output.level.name}: {output.title}[/red]\n" f"    {output.message}")

    if not outputs:
        print("[green]no issues found ✅[/green]")

    raise typer.Exit(1 if outputs else 0)


@app.command(
    name="check",
    short_help="Reformat a descriptor file.",
    help="""
    Reformat a descriptor file.
    """,
)
def format(path: Annotated[Path, typer.Argument(help="The file path")]) -> None:
    raise NotImplementedError()


if __name__ == "__main__":
    app()
