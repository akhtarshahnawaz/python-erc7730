from typing import override

from erc7730.model.context import EIP712JsonSchema

from erc7730.linter.classifier import Classifier, TxClass


class EIP712Classifier(Classifier[EIP712JsonSchema]):
    @override
    def classify(self, schema: EIP712JsonSchema) -> TxClass | None:
        if "permit" in schema.primaryType.lower():
            return TxClass.PERMIT
        return None
