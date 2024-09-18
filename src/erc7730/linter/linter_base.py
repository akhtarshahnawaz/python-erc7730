from erc7730.linter import Linter
from erc7730.model.erc7730_descriptor import ERC7730Descriptor


class MultiLinter(Linter):
    def __init__(self, linters: list[Linter]):
        self.linters = linters

    def lint(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        for linter in self.linters:
            linter.lint(descriptor, out)
