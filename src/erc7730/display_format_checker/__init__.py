from erc7730.classifier import TxClass
from erc7730.linter import Linter
from erc7730.model.display import Display, Format


def _fields_contain(word: str, fields: set[str]) -> bool:
    # check if the word is contained in one of the fields
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
        for format in formats.values():  # format: Format has fields: Optional[Fields]
            if format.fields is not None:
                # format.fields is a dict[str, Union[FieldDescription, ...]]
                for field in format.fields.root.keys():
                    fields.add(str(field))
        return fields

    def check(self) -> list[Linter.Output]:
        res: list[Linter.Output] = []
        match self.c:
            case TxClass.PERMIT:
                formats = self.d.formats
                fields = self._get_all_displayed_fields(formats)
                if not _fields_contain("spender", fields):
                    res.append(
                        Linter.Output(
                            title="Missing spender in displayed fields", message="", level=Linter.Output.Level.ERROR
                        )
                    )
                if not _fields_contain("amount", fields):
                    res.append(
                        Linter.Output(
                            title="Missing amount in displayed fields", message="", level=Linter.Output.Level.ERROR
                        )
                    )
                if (
                    not _fields_contain("valid until", fields)
                    and not _fields_contain("expiry", fields)
                    and not _fields_contain("expiration", fields)
                ):
                    res.append(
                        Linter.Output(
                            title="Missing expiration date in displayed fields",
                            message="",
                            level=Linter.Output.Level.ERROR,
                        )
                    )
        return res
