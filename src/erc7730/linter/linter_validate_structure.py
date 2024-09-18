from erc7730.linter import Linter
from erc7730.model.erc7730_descriptor import ERC7730Descriptor


class ValidateStructureLinter(Linter):
    """
    - for each field, check paths match schema / ABI
    - other checks ???
    """

    def lint(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        pass
