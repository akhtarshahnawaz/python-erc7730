from typing import override

from erc7730.model.context import AbiJsonSchema

from erc7730.linter.classifier import Classifier, TxClass


class ABIClassifier(Classifier[AbiJsonSchema]):
    @override
    def classify(self, schema: AbiJsonSchema) -> TxClass | None:
        pass
