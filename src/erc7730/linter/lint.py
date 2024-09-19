from pathlib import Path

from erc7730.common.pydantic import model_from_json_file
from erc7730.linter import Linter
from erc7730.linter.linter_base import MultiLinter
from erc7730.linter.linter_demo import DemoLinter
from erc7730.linter.linter_transaction_type_classifier_ai import ClassifyTransactionTypeLinter
from erc7730.model.erc7730_descriptor import ERC7730Descriptor
from rich import print

from erc7730.model.utils import resolve_external_references


def lint_all(path: Path, demo: bool = False) -> list[Linter.Output]:
    linters: list[Linter] = [
        # DO_NO_COMMIT: add linters here
        ClassifyTransactionTypeLinter(),
    ]

    if demo:
        linters.append(DemoLinter())

    linter = MultiLinter(linters)

    outputs: list[Linter.Output] = []

    if path.is_file():
        lint_file(path, linter, outputs.append)
    elif path.is_dir():
        for file in path.rglob("*.json"):
            if file.name.startswith("calldata-") or file.name.startswith("eip712-"):
                lint_file(file, linter, outputs.append)
    else:
        raise ValueError(f"Invalid path: {path}")

    return outputs


def lint_file(path: Path, linter: Linter, out: Linter.OutputAdder) -> None:
    print(f"checking {path}...")

    def adder(output: Linter.Output) -> None:
        out(output.model_copy(update={"file": path}))

    try:
        descriptor = model_from_json_file(path, ERC7730Descriptor)
        descriptor = resolve_external_references(descriptor)
        linter.lint(descriptor, adder)
    except Exception as e:
        out(Linter.Output(file=path, title="Failed to parse", message=str(e), level=Linter.Output.Level.ERROR))
