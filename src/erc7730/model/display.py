from erc7730.model.base import BaseLibraryModel
from erc7730.model.types import Id
from typing import Annotated, Any, Dict, ForwardRef, Optional, Union
from enum import StrEnum
from pydantic import Discriminator, RootModel, Field as PydanticField, Tag


class Source(StrEnum):
    WALLET = "wallet"
    ENS = "ens"
    CONTRACT = "contract"
    TOKEN = "token"
    COLLECTION = "collection"


class FieldFormat(StrEnum):
    RAW = "raw"
    ADDRESS_NAME = "addressName"
    CALL_DATA = "calldata"
    AMOUNT = "amount"
    TOKEN_AMOUNT = "tokenAmount"
    NFT_NAME = "nftName"
    DATE = "date"
    DURATION = "duration"
    UNIT = "unit"
    ENUM = "enum"


class FieldsParent(BaseLibraryModel):
    path: str


class Reference(FieldsParent):
    ref: str = PydanticField(alias="$ref")
    params: Optional[dict[str, str]] = None


class TokenAmountParameters(BaseLibraryModel):
    tokenPath: str
    nativeCurrencyAddress: Optional[str] = None
    threshold: Optional[str] = None
    message: Optional[str] = None


class DateEncoding(StrEnum):
    BLOCKHEIGHT = "blockheight"
    TIMESTAMP = "timestamp"


class DateParameters(BaseLibraryModel):
    encoding: DateEncoding


class AddressNameType(StrEnum):
    WALLET = "wallet"
    EOA = "eoa"
    CONTRACT = "contract"
    TOKEN = "token"
    NFT = "nft"


class AddressNameSources(StrEnum):
    LOCAL = "local"
    ENS = "ens"


class AddressNameParameters(BaseLibraryModel):
    type: Optional[AddressNameType] = None
    sources: Optional[list[AddressNameSources]] = None


class CallDataParameters(BaseLibraryModel):
    selector: Optional[str] = None
    calleePath: Optional[str] = None


class NftNameParameters(BaseLibraryModel):
    collectionPath: str


class UnitParameters(BaseLibraryModel):
    base: int
    decimals: Optional[int] = None
    prefix: Optional[bool] = None


class EnumParameters(BaseLibraryModel):
    field_ref: str = PydanticField(alias="$ref")


class FieldDescription(BaseLibraryModel):
    field_id: Optional[Id] = PydanticField(None, alias="$id")
    label: str
    format: FieldFormat
    params: Optional[
        Union[
            AddressNameParameters,
            CallDataParameters,
            TokenAmountParameters,
            NftNameParameters,
            DateParameters,
            UnitParameters,
            EnumParameters,
        ]
    ] = None


class NestedFields(FieldsParent):
    fields: Optional[list[ForwardRef("Field")]] = None  # type: ignore


def get_discriminator_value(v: Any) -> str:
    if isinstance(v, dict):
        if v.get("$ref") is not None:
            return "reference"
        if v.get("label") is not None and v.get("format") is not None:
            return "field_description"
        if v.get("fields") is not None:
            return "nested_fields"
    return ""


class Field(
    RootModel[
        Annotated[
            Union[
                Annotated[Reference, Tag("reference")],
                Annotated[FieldDescription, Tag("field_description")],
                Annotated[NestedFields, Tag("nested_fields")],
            ],
            Discriminator(get_discriminator_value),
        ]
    ]
):
    """Field"""


NestedFields.model_rebuild()


class Screen(BaseLibraryModel):
    pass


class Format(BaseLibraryModel):
    field_id: Optional[Id] = PydanticField(None, alias="$id")
    intent: Optional[Union[str, Dict[str, str]]] = None
    fields: Optional[list[Field]] = None
    required: Optional[list[str]] = None
    screens: Optional[dict[str, list[Screen]]] = None


class Display(BaseLibraryModel):
    definitions: Optional[dict[str, FieldDescription]] = None
    formats: dict[str, Format]
