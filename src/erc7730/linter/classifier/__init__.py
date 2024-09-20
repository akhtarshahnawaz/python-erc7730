from abc import ABC, abstractmethod
from enum import StrEnum, auto
from typing import TypeVar, Generic

from erc7730.model.context import EIP712JsonSchema, AbiJsonSchema


class TxClass(StrEnum):
    STAKE = auto()
    SWAP = auto()
    PERMIT = auto()
    WITHDRAW = auto()


Schema = TypeVar("Schema", AbiJsonSchema, EIP712JsonSchema)


class Classifier(ABC, Generic[Schema]):
    @abstractmethod
    def classify(self, schema: Schema) -> TxClass | None:
        raise NotImplementedError()
