from typing import override

from erc7730.model.context import EIP712JsonSchema

from erc7730.classifier import Classifier, TxClass


class EIP712Classifier(Classifier):
    @override
    def classify(self, schema: EIP712JsonSchema) -> TxClass | None:
        pass
