from eip-712-erc-7730.model.base import BaseLibraryModel
from typing import Optional
from typing import Union
from enum import StrEnum



class Source(StrEnum):
    WALLET = "wallet"
    ENS = "ens"
    CONTRACT = "contract"
    TOKEN = "token"
    COLLECTION = "collection"

class Format(StrEnum):
    ADDRESS_NAME = "addressName"
    NFT_NAME = "nftName"
    TOKEN_NAME = "tokenAmount"
    ALLOWANCE_AMOUNT = "allowanceAmount"
    PERCENTAGE = "percentage"
    DATE = "date"
    ENUM = "enum"

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
    id: Optional[Id] = None
    label: str
    format: Format
    sources: Optional[list[Source]] = None
    collectionPath: Optional[str] = None
    tokenAmountParameters: Optional[TokenAmountParameters] = None
    allowanceAmountParameters: Optional[AllowanceAmountParameters] = None
    percentageParameters: Optional[PercentageParameters] = None
    dateParameters: Optional[DateParameters] = None
    enumParameters: Optional[str] = None


class Display(BaseLibraryModel):
    definitions: Optional[list[Field]]= None
    formats: list[Format]


