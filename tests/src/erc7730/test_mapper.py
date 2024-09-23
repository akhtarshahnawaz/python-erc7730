# from pathlib import Path
# from erc7730.common.pydantic import model_from_json_file_or_none
# from erc7730.model.erc7730_descriptor import ERC7730Descriptor
# from erc7730.mapper.mapper import to_eip712_mapper, to_erc7730_mapper
# mport pytest
# import glob

# files = glob.glob('clear-signing-erc7730-registry/registry/*/eip712*.json')

"""@pytest.mark.parametrize("file", files)
def roundtrip(file: str) -> None:
    erc7730Descriptor = model_from_json_file_or_none(Path(file), ERC7730Descriptor)
    assert erc7730Descriptor is not None
    eip712DappDescriptor = to_eip712_mapper(erc7730Descriptor)
    assert eip712DappDescriptor is not None
    newErc7730Descriptor = to_erc7730_mapper(eip712DappDescriptor)
    assert newErc7730Descriptor is not None
    assert newErc7730Descriptor == erc7730Descriptor

def test_to_eip712_mapper() -> None:
    uniswap_eip712_cs_descriptor = model_from_json_file_or_none(Path("clear-signing-erc7730-registry/registry/uniswap/eip712-permit2.json"), ERC7730Descriptor)
    assert uniswap_eip712_cs_descriptor is not None
    eip712DappDescriptor = to_eip712_mapper(uniswap_eip712_cs_descriptor)
    assert eip712DappDescriptor is not None
    assert eip712DappDescriptor.chain_id == 1
    assert eip712DappDescriptor.name == "Permit2"
    assert eip712DappDescriptor.contracts.__len__() == 2
    assert eip712DappDescriptor.contracts[0].messages.__len__() == 1"""
