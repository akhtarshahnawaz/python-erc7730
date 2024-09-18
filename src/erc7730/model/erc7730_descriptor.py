from erc7730.model.base import BaseLibraryModel
from erc7730.model.context import ContractContext, EIP712Context
from erc7730.model.display import Display
from erc7730.model.metadata import Metadata
from pydantic import ConfigDict, AnyUrl
from pathlib import Path
from typing import Union, Optional


class ERC7730Descriptor(BaseLibraryModel):
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        extra="forbid",
        revalidate_instances="always",
        validate_default=True,
        validate_return=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        allow_inf_nan=False,
    )
    context: Optional[Union[ContractContext, EIP712Context]] = None
    includes: Optional[list[Union[AnyUrl, Path]]] = None
    metadata: Optional[Metadata] = None
    display: Optional[Display] = None
