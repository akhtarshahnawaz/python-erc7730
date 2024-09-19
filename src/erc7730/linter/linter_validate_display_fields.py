from erc7730.common.abi import compute_paths, compute_selector
from erc7730.common.erc7730 import compute_eip712_paths, compute_format_paths
from erc7730.linter import Linter
from erc7730.model.context import ContractContext, EIP712Context, EIP712JsonSchema
from erc7730.model.erc7730_descriptor import ERC7730Descriptor


class ValidateDisplayFieldsLinter(Linter):
    """
    - for each field of schema/ABI, check that there is a display field
    - for each field, check that display configuration is relevant with field type
    """

    def _validate_eip712_paths(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        if (
            descriptor.context is not None
            and descriptor.display is not None
            and isinstance(descriptor.context, EIP712Context)
            and descriptor.context.eip712.schemas is not None
        ):
            primary_types: set[str] = set()
            for schema in descriptor.context.eip712.schemas:
                if isinstance(schema, EIP712JsonSchema):
                    primary_types.add(schema.primaryType)
                    if schema.primaryType not in schema.types:
                        out(
                            Linter.Output(
                                title="Invalid EIP712 Schema",
                                message=f"Primary type `{schema.primaryType}` not found in types.",
                                level=Linter.Output.Level.ERROR,
                            )
                        )
                        continue
                    if schema.primaryType not in descriptor.display.formats:
                        out(
                            Linter.Output(
                                title="Missing Display field",
                                message=f"Display field for primary type `{schema.primaryType}` is missing.",
                                level=Linter.Output.Level.WARNING,
                            )
                        )
                        continue
                    eip712_paths = compute_eip712_paths(schema)
                    format_paths = compute_format_paths(descriptor.display.formats[schema.primaryType]).data_paths

                    for path in eip712_paths - format_paths:
                        out(
                            Linter.Output(
                                title="Missing Display field",
                                message=f"Display field for path `{path}` is missing for message {schema.primaryType}.",
                                level=Linter.Output.Level.WARNING,
                            )
                        )
                    for path in format_paths - eip712_paths:
                        out(
                            Linter.Output(
                                title="Extra Display field",
                                message=f"Display field for path `{path}` is not in message {schema.primaryType}.",
                                level=Linter.Output.Level.ERROR,
                            )
                        )

                else:
                    out(
                        Linter.Output(
                            title="Missing EIP712 Schema",
                            message=f"EIP712 Schema is missing (found {schema})",
                            level=Linter.Output.Level.ERROR,
                        )
                    )

            for fmt in descriptor.display.formats.keys():
                if fmt not in primary_types:
                    out(
                        Linter.Output(
                            title="Invalid Display field",
                            message=f"Format message `{fmt}` is not in EIP712 schemas.",
                            level=Linter.Output.Level.ERROR,
                        )
                    )

    def _validate_abi_paths(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        if (
            descriptor.context is not None
            and descriptor.display is not None
            and isinstance(descriptor.context, ContractContext)
            and isinstance(descriptor.context.contract.abi, list)
        ):
            abi_paths_by_selector: dict[str, set[str]] = {}
            for abi in descriptor.context.contract.abi:
                if abi.type == "function":
                    abi_paths_by_selector[compute_selector(abi)] = compute_paths(abi)

            for selector, fmt in descriptor.display.formats.items():
                if selector not in abi_paths_by_selector:
                    out(
                        Linter.Output(
                            title="Invalid selector",
                            message=f"Selector {selector} not found in ABI.",
                            level=Linter.Output.Level.ERROR,
                        )
                    )
                    continue
                format_paths = compute_format_paths(fmt).data_paths
                abi_paths = abi_paths_by_selector[selector]

                for path in abi_paths - format_paths:
                    out(
                        Linter.Output(
                            title="Missing Display field",
                            message=f"Display field for path `{path}` is missing for selector {selector}.",
                            level=Linter.Output.Level.WARNING,
                        )
                    )
                for path in format_paths - abi_paths:
                    out(
                        Linter.Output(
                            title="Invalid Display field",
                            message=f"Display field for path `{path}` is not in selector {selector}.",
                            level=Linter.Output.Level.ERROR,
                        )
                    )

    def lint(self, descriptor: ERC7730Descriptor, out: Linter.OutputAdder) -> None:
        self._validate_eip712_paths(descriptor, out)
        self._validate_abi_paths(descriptor, out)
