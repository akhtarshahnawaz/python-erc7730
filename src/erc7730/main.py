from pathlib import Path
from typing import Annotated, List

import typer

from rich import print as rprint

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
    paths: Annotated[List[Path], typer.Argument(help="The files or directory paths to lint")],
    gha: Annotated[bool, typer.Option(help="Enable Github annotations output")] = False,
) -> None:
    from erc7730.linter.lint import lint_all
    from erc7730.linter import ERC7730Linter

    outputs = lint_all(paths)

    for output in outputs:
        p = output.file.name if output.file is not None else "unknown file"
        if gha:
            # msg = f"{output.title} {output.message}"
            match output.level:
                case ERC7730Linter.Output.Level.INFO:
                    print(f"::notice file={output.file},title={output.title}::{output.message}")
                case ERC7730Linter.Output.Level.WARNING:
                    print(f"::warning file={output.file},title={output.title}::{output.message}")
                case ERC7730Linter.Output.Level.ERROR:
                    print(f"::error file={output.file},title={output.title}::{output.message}")
        else:
            match output.level:
                case ERC7730Linter.Output.Level.INFO:
                    rprint(f"[blue]{p}: {output.level.name}: {output.title}[/blue]\n" f"    {output.message}")
                case ERC7730Linter.Output.Level.WARNING:
                    rprint(f"[yellow]{p}: {output.level.name}: {output.title}[/yellow]\n" f"    {output.message}")
                case ERC7730Linter.Output.Level.ERROR:
                    rprint(f"[red]{p}: {output.level.name}: {output.title}[/red]\n" f"    {output.message}")

    if not outputs:
        rprint("[green]no issues found ✅[/green]")

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
