from abc import ABC, abstractmethod
from enum import StrEnum, auto
from typing import Union

from erc7730.model.context import EIP712JsonSchema, AbiJsonSchema


class TxClass(StrEnum):
    STAKE = auto()
    SWAP = auto()
    PERMIT = auto()
    WITHDRAW = auto()


class Classifier(ABC):
    @abstractmethod
    def classify(self, schema: Union[AbiJsonSchema, EIP712JsonSchema]) -> TxClass | None:
        raise NotImplementedError()
