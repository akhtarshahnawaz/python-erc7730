from pathlib import Path
from erc7730.common.pydantic import model_from_json_file_or_none
from erc7730.model.erc7730_descriptor import ERC7730Descriptor
from erc7730.mapper.mapper import to_eip712_mapper


def test_to_eip712_mapper() -> None:
    uniswap_eip712_cs_descriptor = model_from_json_file_or_none(Path("clear-signing-erc7730-registry/registry/uniswap/eip712-permit2.json"), ERC7730Descriptor)
    assert uniswap_eip712_cs_descriptor is not None
    eip712_mapper = to_eip712_mapper(uniswap_eip712_cs_descriptor)
    assert eip712_mapper is not None
    assert eip712_mapper.chain_id == 1
    assert eip712_mapper.name == "Permit2"
    assert eip712_mapper.contracts.__len__() == 2
    assert eip712_mapper.contracts[0].messages.__len__() == 1
