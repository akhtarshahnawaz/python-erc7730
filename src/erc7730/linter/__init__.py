from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import IntEnum, auto
from typing import Self

from erc7730.model.erc7730_descriptor import ERC7730Descriptor

from pydantic import BaseModel, FilePath


class Linter(ABC):
    @abstractmethod
    def lint(self, descriptor: ERC7730Descriptor, out: "OutputAdder") -> None:
        raise NotImplementedError()

    class Output(BaseModel):
        class Level(IntEnum):
            INFO = auto()
            WARNING = auto()
            ERROR = auto()

        file: FilePath
        line: int
        title: str
        message: str
        level: Level

    OutputAdder = Callable[[Output], None]
