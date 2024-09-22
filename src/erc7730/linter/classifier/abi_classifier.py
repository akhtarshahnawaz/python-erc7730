from typing_extensions import override

from erc7730.model.context import AbiJsonSchema

from erc7730.linter.classifier import Classifier, TxClass


class ABIClassifier(Classifier[AbiJsonSchema]):
    """
    Given an EIP712 schema, classify the transaction type with some predefined ruleset.
    (not implemented)
    """

    @override
    def classify(self, schema: AbiJsonSchema) -> TxClass | None:
        pass
