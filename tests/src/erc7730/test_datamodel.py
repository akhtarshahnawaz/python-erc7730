from pathlib import Path
from erc7730.common.pydantic import model_from_json_file_or_none
from erc7730.model.erc7730_descriptor import ERC7730Descriptor

def test_from_erc7730() -> None:
    assert model_from_json_file_or_none(Path("clear-signing-erc7730-registry/registry/makerdao/eip712-permit-DAI.json"), ERC7730Descriptor) is not None
    assert model_from_json_file_or_none(Path("clear-signing-erc7730-registry/registry/aave/calldata-lpv2.json"), ERC7730Descriptor) is not None
    assert model_from_json_file_or_none(Path("clear-signing-erc7730-registry/registry/lido/calldata-stETH.json"), ERC7730Descriptor) is not None
    assert model_from_json_file_or_none(Path("clear-signing-erc7730-registry/registry/lido/calldata-wstETH.json"), ERC7730Descriptor) is not None
    assert model_from_json_file_or_none(Path("clear-signing-erc7730-registry/registry/paraswap/calldata-AugustusSwapper.json"), ERC7730Descriptor) is not None
    assert model_from_json_file_or_none(Path("clear-signing-erc7730-registry/registry/tether/calldata-usdt.json"), ERC7730Descriptor) is not None
    assert model_from_json_file_or_none(Path("clear-signing-erc7730-registry/registry/uniswap/calldata-UniswapV3Router02.json"), ERC7730Descriptor) is not None
    assert model_from_json_file_or_none(Path("clear-signing-erc7730-registry/registry/uniswap/eip712-permit2.json"), ERC7730Descriptor) is not None