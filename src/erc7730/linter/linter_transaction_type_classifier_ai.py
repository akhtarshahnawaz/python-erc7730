from erc7730.linter import Linter
from erc7730.model.erc7730_descriptor import ERC7730Descriptor


class ClassifyTransactionTypeLinter(Linter):
    """
    - given schema/ABI, classify the transaction type
    - if class found, check descriptor display fields against predefined ruleset
    - possible class (swap, staking withdraw, staking deposit)
    """

    def lint(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        pass
