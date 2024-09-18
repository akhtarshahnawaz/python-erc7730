from erc7730.linter import Linter
from erc7730.model.erc7730_descriptor import ERC7730Descriptor


class ValidateDisplayFieldsLinter(Linter):
    """
    - for each field of schema/ABI, check that there is a display field
    - for each field, check that display configuration is relevant with field type
    """

    def lint(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        pass
