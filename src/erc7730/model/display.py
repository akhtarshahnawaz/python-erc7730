from erc7730.model.base import BaseLibraryModel
from erc7730.model.types import Id
from typing import Dict, ForwardRef, Optional, Union
from enum import StrEnum
from pydantic import RootModel, Field as PydanticField


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
    ref: Optional[str] = PydanticField(None, alias="$ref")
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
    label: Optional[str] = None
    format: Optional[FieldFormat] = None
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
    fields: Optional[ForwardRef("Fields")] = None  # type: ignore


class Fields(RootModel[Union[Reference, FieldDescription, NestedFields]]):
    """Fields"""


NestedFields.model_rebuild()


class Screen(BaseLibraryModel):
    pass


class Format(BaseLibraryModel):
    field_id: Optional[Id] = PydanticField(None, alias="$id")
    intent: Optional[Union[str, Dict[str, str]]] = None
    fields: Optional[list[Fields]] = None
    required: Optional[list[str]] = None
    screens: Optional[dict[str, list[Screen]]] = None


class Display(BaseLibraryModel):
    definitions: Optional[dict[str, FieldDescription]] = None
    formats: dict[str, Format]
