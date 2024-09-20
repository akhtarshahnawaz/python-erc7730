from erc7730.linter.classifier import TxClass
from erc7730.linter import ERC7730Linter
from erc7730.model.display import Display, Format


def _fields_contain(word: str, fields: set[str]) -> bool:
    """
    to check if the provided keyword is contained in one of the fields (case insensitive)
    """
    for field in fields:
        if word.lower() in field.lower():
            return True
    return False


class DisplayFormatChecker:
    def __init__(self, c: TxClass, d: Display):
        self.c = c
        self.d = d

    def _get_all_displayed_fields(self, formats: dict[str, Format]) -> set[str]:
        fields: set[str] = set()
        for format in formats.values():
            if format.fields is not None:
                for field in format.fields.root.keys():
                    fields.add(str(field))
        return fields

    def check(self) -> list[ERC7730Linter.Output]:
        res: list[ERC7730Linter.Output] = []
        match self.c:
            case TxClass.PERMIT:
                formats = self.d.formats
                fields = self._get_all_displayed_fields(formats)
                if not _fields_contain("spender", fields):
                    res.append(
                        ERC7730Linter.Output(
                            title="Missing spender in displayed fields",
                            message="",
                            level=ERC7730Linter.Output.Level.ERROR,
                        )
                    )
                if not _fields_contain("amount", fields):
                    res.append(
                        ERC7730Linter.Output(
                            title="Missing amount in displayed fields",
                            message="",
                            level=ERC7730Linter.Output.Level.ERROR,
                        )
                    )
                if (
                    not _fields_contain("valid until", fields)
                    and not _fields_contain("expiry", fields)
                    and not _fields_contain("expiration", fields)
                ):
                    res.append(
                        ERC7730Linter.Output(
                            title="Field not displayed",
                            message="Missing expiration date in displayed fields for permit",
                            level=ERC7730Linter.Output.Level.ERROR,
                        )
                    )
        return res
