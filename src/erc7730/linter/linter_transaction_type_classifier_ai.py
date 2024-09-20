from erc7730.linter.classifier.abi_classifier import ABIClassifier
from erc7730.linter.classifier.eip712_classifier import EIP712Classifier
from erc7730.linter.common.display_format_checker import DisplayFormatChecker
from erc7730.linter import ERC7730Linter
from erc7730.model.context import EIP712Context, ContractContext, EIP712JsonSchema
from erc7730.model.display import Display
from erc7730.model.erc7730_descriptor import ERC7730Descriptor

from erc7730.linter.classifier import TxClass
from pydantic import AnyUrl


def determine_tx_class(descriptor: ERC7730Descriptor) -> TxClass | None:
    if isinstance(descriptor.context, EIP712Context):
        classifier = EIP712Classifier()
        if descriptor.context.eip712.schemas is not None:
            first_schema = descriptor.context.eip712.schemas[0]
            if isinstance(first_schema, EIP712JsonSchema):
                return classifier.classify(first_schema)
            # url should have been resolved earlier
    elif isinstance(descriptor.context, ContractContext):
        abi_classifier = ABIClassifier()
        if descriptor.context.contract.abi is not None:
            abi_schema = descriptor.context.contract.abi
            if abi_schema is not None and not isinstance(abi_schema, AnyUrl):
                return abi_classifier.classify(abi_schema)
            # url should have been resolved earlier
    return None


class ClassifyTransactionTypeLinter(ERC7730Linter):
    """
    - given schema/ABI, classify the transaction type
    - if class found, check descriptor display fields against predefined ruleset
    - possible class (swap, staking withdraw, staking deposit)
    """

    def lint(self, descriptor: ERC7730Descriptor, out: ERC7730Linter.OutputAdder) -> None:
        if descriptor.context is None:
            return None
        c = determine_tx_class(descriptor)
        if c is None:
            # could not determine transaction type
            return None
        out(ERC7730Linter.Output(title="Transaction type: ", message=str(c), level=ERC7730Linter.Output.Level.INFO))
        d: Display | None = descriptor.display
        if d is None:
            return None
        display_format_checker: DisplayFormatChecker = DisplayFormatChecker(c, d)
        linter_outputs = display_format_checker.check()
        for linter_output in linter_outputs:
            out(linter_output)
