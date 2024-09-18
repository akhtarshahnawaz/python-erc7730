from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import IntEnum, auto

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

        file: FilePath | None = None
        line: int | None = None
        title: str
        message: str
        level: Level = Level.ERROR

    OutputAdder = Callable[[Output], None]
