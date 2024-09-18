from pathlib import Path
from erc7730.common.pydantic import model_from_json_file_or_none
from erc7730.model.erc7730_descriptor import ERC7730Descriptor
import pytest
import glob

files = glob.glob("clear-signing-erc7730-registry/registry/*/*.json")


@pytest.mark.parametrize("file", files)
def test_from_erc7730(file: str) -> None:
    assert model_from_json_file_or_none(Path(file), ERC7730Descriptor) is not None
