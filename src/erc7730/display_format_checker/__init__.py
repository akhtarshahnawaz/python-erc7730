from erc7730.classifier import TxClass
from erc7730.linter import Linter
from erc7730.model.display import Display, Format


class DisplayFormatChecker:
    def __init__(self, c: TxClass, d: Display):
        self.c = c
        self.d = d

    def _get_all_displayed_labels(self, formats: dict[str, Format]) -> set[str]:
        labels: set[str] = set()
        #        for format in formats.values():    # format: Format has fields: Optional[Fields]
        #            if format.fields is not None:
        #                format.fields is a dict[str, Union[Reference, Field, StructFormats]]
        #                for field in format.fields.values():
        #                    labels.append(field.label.lower())
        return labels

    def check(self) -> list[Linter.Output]:
        match self.c:
            case TxClass.PERMIT:
                formats = self.d.formats
                labels = self._get_all_displayed_labels(formats)
                if "spender" not in labels:
                    return [
                        Linter.Output(
                            title="Missing spender in displayed fields", message="", level=Linter.Output.Level.ERROR
                        )
                    ]
                if "amount" not in labels:
                    return [
                        Linter.Output(
                            title="Missing amount in displayed fields", message="", level=Linter.Output.Level.ERROR
                        )
                    ]
                if "valid until" not in labels and "expiry" not in labels and "expiration" not in labels:
                    return [
                        Linter.Output(
                            title="Missing expiration date in displayed fields",
                            message="",
                            level=Linter.Output.Level.ERROR,
                        )
                    ]
                return []
        return []
