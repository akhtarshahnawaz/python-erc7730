from eip-712-erc-7730.model.base import BaseLibraryModel
from eip-712-erc-7730.model.context import Context
from eip-712-erc-7730.model.display import Display
from pydantic import ConfigDict, AnyUrl

class ERC7730Descriptor(BaseLibraryModel):
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        extra="ignore",
        revalidate_instances="always",
        validate_default=True,
        validate_return=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        allow_inf_nan=False,
    )
    context: Context
    includes: list[AnyUrl]
    metadata: Metadata
    display: Display