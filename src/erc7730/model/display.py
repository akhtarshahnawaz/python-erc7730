from erc7730.model.base import BaseLibraryModel
from erc7730.model.types import Id
from typing import ForwardRef, Optional, Dict, Union
from enum import StrEnum
from pydantic import RootModel, Field as PydanticField



class Source(StrEnum):
    WALLET = "wallet"
    ENS = "ens"
    CONTRACT = "contract"
    TOKEN = "token"
    COLLECTION = "collection"

class FieldFormat(StrEnum):
    ADDRESS_NAME = "addressName"
    NFT_NAME = "nftName"
    TOKEN_NAME = "tokenAmount"
    ALLOWANCE_AMOUNT = "allowanceAmount"
    PERCENTAGE = "percentage"
    DATE = "date"
    ENUM = "enum"

class Reference(BaseLibraryModel):
    ref: str = PydanticField(alias='$ref')
    params: Optional[Dict[str, str]]

class TokenAmountParameters(BaseLibraryModel):
    tokenPath: str
    nativeCurrencyAddress: Optional[str] = None

class DateEncoding(StrEnum):
     BLOCKHEIGHT = "blockheight"
     TIMESTAMP = "timestamp"    

class DateParameters(BaseLibraryModel):
    encoding: DateEncoding

class PercentageParameters(BaseLibraryModel):
        magnitude: int

class AllowanceAmountParameters(BaseLibraryModel):
    tokenPath: str
    threshold: str
    nativeCurrencyAddress:Optional[str] = None

class Field(BaseLibraryModel):
    sources: Optional[list[Source]] = None
    collectionPath: Optional[str] = None
    tokenAmountParameters: Optional[TokenAmountParameters] = None
    allowanceAmountParameters: Optional[AllowanceAmountParameters] = None
    percentageParameters: Optional[PercentageParameters] = None
    dateParameters: Optional[DateParameters] = None
    enumParameters: Optional[str] = None

class FieldDescription(BaseLibraryModel):
    id: Optional[Id]
    label: str
    format: FieldFormat
    params: Optional[Field]

class StructFormats(BaseLibraryModel):
     fields: ForwardRef('Fields') # type: ignore

class Fields(RootModel[Dict[str, Union[Reference, Field, StructFormats]]]):
    """ todo use StructFormats instead """
StructFormats.model_rebuild()

class Screen(BaseLibraryModel):
    pass

class Format(BaseLibraryModel):
     id: Optional[Id] = None
     intent: Optional[str] = None
     fields: Optional[Fields] = None
     required: Optional[list[str]] = None
     screens: Optional[Dict[str, list[Screen]]] = None



class Display(BaseLibraryModel):
    definitions: Optional[Dict[str, Field]] = None
    formats: Dict[str, Format]
