from erc7730.linter import Linter
from erc7730.model.erc7730_descriptor import ERC7730Descriptor


class CheckImpactsLinter(Linter):
    """
    - get example transactions (source can be descriptor or *scan)
    - simulate with blockaid (or atlas)
    - compare the impacts with the descriptor
    """

    def lint(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        pass
