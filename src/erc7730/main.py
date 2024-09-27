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
convert_app = typer.Typer(
    name="convert",
    no_args_is_help=True,
    short_help="Commands to convert descriptor files.",
    help="""
    Commands to convert descriptor files.
    """,
)
app.add_typer(convert_app)


@app.command(
    name="lint",
    short_help="Validate descriptor files.",
    help="""
    Validate descriptor files.
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
            msg = output.message.replace("\n", "%0A")
            match output.level:
                case ERC7730Linter.Output.Level.INFO:
                    print(f"::notice file={output.file},title={output.title}::{msg}")
                case ERC7730Linter.Output.Level.WARNING:
                    print(f"::warning file={output.file},title={output.title}::{msg}")
                case ERC7730Linter.Output.Level.ERROR:
                    print(f"::error file={output.file},title={output.title}::{msg}")
        else:
            match output.level:
                case ERC7730Linter.Output.Level.INFO:
                    rprint(f"[blue]{p}: {output.level.name}: {output.title}[/blue]\n    {output.message}")
                case ERC7730Linter.Output.Level.WARNING:
                    rprint(f"[yellow]{p}: {output.level.name}: {output.title}[/yellow]\n    {output.message}")
                case ERC7730Linter.Output.Level.ERROR:
                    rprint(f"[red]{p}: {output.level.name}: {output.title}[/red]\n    {output.message}")

    if not outputs:
        rprint("[green]no issues found ✅[/green]")

    raise typer.Exit(1 if outputs else 0)


@convert_app.command(
    name="eip712-to-erc7730",
    short_help="Convert a legacy EIP-712 descriptor file to an ERC-7730 file.",
    help="""
    Convert a legacy EIP-712 descriptor file to an ERC-7730 file.
    """,
)
def convert_eip712_to_erc7730(
    input_eip712_path: Annotated[Path, typer.Argument(help="The input EIP-712 file path")],
    output_erc7730_path: Annotated[Path, typer.Argument(help="The output ERC-7730 file path")],
) -> None:
    # TODO BACK-7687: implement conversion from EIP-712 to ERC-7730 descriptors
    raise NotImplementedError()


@convert_app.command(
    name="erc7730-to-eip712",
    short_help="Convert an ERC-7730 file to a legacy EIP-712 descriptor file.",
    help="""
    Convert an ERC-7730 file to a legacy EIP-712 descriptor file (if applicable).
    """,
)
def convert_erc7730_to_eip712(
    input_erc7730_path: Annotated[Path, typer.Argument(help="The input ERC-7730 file path")],
    output_eip712_path: Annotated[Path, typer.Argument(help="The output EIP-712 file path")],
) -> None:
    # TODO BACK-7686: implement conversion from ERC-7730 to EIP-712 descriptors
    raise NotImplementedError()


if __name__ == "__main__":
    app()
