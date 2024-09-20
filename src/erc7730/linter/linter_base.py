from erc7730.linter import ERC7730Linter
from erc7730.model.erc7730_descriptor import ERC7730Descriptor


class MultiLinter(ERC7730Linter):
    def __init__(self, linters: list[ERC7730Linter]):
        self.linters = linters

    def lint(self, descriptor: ERC7730Descriptor, out: ERC7730Linter.OutputAdder) -> None:
        for linter in self.linters:
            linter.lint(descriptor, out)
