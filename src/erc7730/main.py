from pathlib import Path
from typing import Annotated

import typer

from erc7730.common.pydantic import model_from_json_file
from erc7730.linter import Linter
from erc7730.linter.linter_check_impacts import CheckImpactsLinter
from erc7730.linter.linter_transaction_type_classifier_ai import ClassifyTransactionTypeLinter
from erc7730.linter.linter_validate_abi import ValidateABILinter
from erc7730.linter.linter_validate_display_fields import ValidateDisplayFieldsLinter
from erc7730.linter.linter_validate_structure import ValidateStructureLinter
from erc7730.model.erc7730_descriptor import ERC7730Descriptor
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
def lint(path: Annotated[Path, typer.Argument(help="The file path")]) -> None:
    from erc7730.linter.linter_base import MultiLinter

    descriptor = model_from_json_file(path, ERC7730Descriptor)

    outputs: list[Linter.Output] = []

    linter = MultiLinter(
        [
            ValidateABILinter(),
            ValidateStructureLinter(),
            ValidateDisplayFieldsLinter(),
            ClassifyTransactionTypeLinter(),
            CheckImpactsLinter(),
        ]
    )

    linter.lint(descriptor, outputs.append)

    for output in outputs:
        print(f"[red]{output.level.name}: line {output.line}: {output.title} {output.message}[/red]")

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
