from erc7730.linter import Linter
from erc7730.model.erc7730_descriptor import ERC7730Descriptor


class ValidateABILinter(Linter):
    """
    - resolves the ABI from the descriptor (URL or provided)
    - resolves the ABI from *scan (given chainId and address of descriptor)
    - => compare the two ABIs
    """

    def lint(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        pass
