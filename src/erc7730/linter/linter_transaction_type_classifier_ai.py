from erc7730.classifier.eip712_classifier import EIP712Classifier
from erc7730.display_format_checker import DisplayFormatChecker
from erc7730.linter import Linter
from erc7730.model.context import EIP712JsonSchema
from erc7730.model.display import Display
from erc7730.model.erc7730_descriptor import ERC7730Descriptor

from erc7730.classifier import TxClass, Classifier


def determine_tx_class(descriptor: ERC7730Descriptor) -> TxClass | None:
    if descriptor.context.eip712 is not None:
        classifier: Classifier = EIP712Classifier()
        first_schema: EIP712JsonSchema = descriptor.context.eip712.schemas[0]
        return classifier.classify(first_schema)
    elif descriptor.context.abi is not None:
        classifier: Classifier = EIP712Classifier()
        first_schema: EIP712JsonSchema = descriptor.context.contract.abi[0]
        return classifier.classify(first_schema)
    else:
        return None


class ClassifyTransactionTypeLinter(Linter):
    """
    - given schema/ABI, classify the transaction type
    - if class found, check descriptor display fields against predefined ruleset
    - possible class (swap, staking withdraw, staking deposit)
    """

    def lint(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        if descriptor.context is None:
            return None
        c = determine_tx_class(descriptor)
        if c is None:
            return None
        d: Display = descriptor.display
        display_format_checker: DisplayFormatChecker = DisplayFormatChecker(c, d)
        linter_outputs = display_format_checker.check()
        for linter_output in linter_outputs:
            out(linter_output)
