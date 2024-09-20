from erc7730.common.client.etherscan import get_contract_abis
from erc7730.common.abi import get_functions, compute_signature
from erc7730.linter import ERC7730Linter
from erc7730.model.context import EIP712Context, ContractContext
from erc7730.model.erc7730_descriptor import ERC7730Descriptor


class ValidateABILinter(ERC7730Linter):
    """
    - resolves the ABI from the descriptor (URL or provided)
    - resolves the ABI from *scan (given chainId and address of descriptor)
    - => compare the two ABIs
    """

    def lint(self, descriptor: ERC7730Descriptor, out: ERC7730Linter.OutputAdder) -> None:
        if isinstance(descriptor.context, EIP712Context):
            return self._validate_eip712_schemas(descriptor.context, out)
        if isinstance(descriptor.context, ContractContext):
            return self._validate_contract_abis(descriptor.context, out)
        raise ValueError("Invalid context type")

    @classmethod
    def _validate_eip712_schemas(cls, context: EIP712Context, out: ERC7730Linter.OutputAdder) -> None:
        pass  # not implemented

    @classmethod
    def _validate_contract_abis(cls, context: ContractContext, out: ERC7730Linter.OutputAdder) -> None:
        if not isinstance(context.contract.abi, list):
            raise ValueError("Contract ABIs should have been resolved")

        if (address := context.contract.address) is None:
            return
        if (abis := get_contract_abis(address)) is None:
            return

        etherscan_abis = get_functions(abis)
        contract_abis = get_functions(context.contract.abi)

        if etherscan_abis.proxy:
            out(
                ERC7730Linter.Output(
                    title="Proxy contract",
                    message="Contract ABI on Etherscan is likely to be a proxy, validation skipped",
                    level=ERC7730Linter.Output.Level.INFO,
                )
            )
            return

        for selector, abi in contract_abis.functions.items():
            if selector not in etherscan_abis.functions:
                out(
                    ERC7730Linter.Output(
                        title="Missing function",
                        message=f"Function `{selector}/{compute_signature(abi)}` is not defined in Etherscan ABI",
                        level=ERC7730Linter.Output.Level.ERROR,
                    )
                )
            else:
                if contract_abis.functions[selector] != etherscan_abis.functions[selector]:
                    out(
                        ERC7730Linter.Output(
                            title="Function mismatch",
                            message=f"Function `{selector}/{compute_signature(abi)}` does not match Etherscan ABI",
                            level=ERC7730Linter.Output.Level.WARNING,
                        )
                    )
