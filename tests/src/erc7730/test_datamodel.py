from pathlib import Path
from erc7730.common.pydantic import model_from_json_file_or_none
from erc7730.model.erc7730_descriptor import ERC7730Descriptor
from erc7730.model.base import BaseLibraryModel

def test_from_erc7730() -> None:
    print(model_from_json_file_or_none(Path("tests/resources/eip712-permit-DAI.json"), BaseLibraryModel))
    assert model_from_json_file_or_none(Path("tests/resources/eip712-permit-DAI.json"), ERC7730Descriptor) is not None