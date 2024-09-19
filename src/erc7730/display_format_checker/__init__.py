from erc7730.classifier import TxClass
from erc7730.linter import Linter
from erc7730.model.display import Display


class DisplayFormatChecker:
    def __init__(self, c: TxClass, d: Display):
        self.c = c
        self.d = d

    def check(self) -> list[Linter.Output]:
        return []
