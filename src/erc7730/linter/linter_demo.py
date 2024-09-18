from erc7730.linter import Linter
from erc7730.model.erc7730_descriptor import ERC7730Descriptor


class DemoLinter(Linter):
    """
    Demo linter that generates dummy outputs.
    """

    def lint(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        out(Linter.Output(title="Demo info", message="This is a demo info message", level=Linter.Output.Level.INFO))
        out(
            Linter.Output(
                title="Demo warning", message="This is a demo warning message", level=Linter.Output.Level.WARNING
            )
        )
        out(Linter.Output(title="Demo error", message="This is a demo error message", level=Linter.Output.Level.ERROR))
