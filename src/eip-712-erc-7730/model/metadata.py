import datetime from datetime
from enum import StrEnum
from pydantic import AnyUrl
from typing import Optional
from eip-712-erc-7730.model.types import Enum

class Metadata(BaseLibraryModel):
    owner: str
    info: OwnerInfo
    token: TokenInfo
    constants: list[str]
    enums: Union[AnyUrl, Enum]

class OwnerInfo(BaseLibraryModel):
    legalName: Optional[str] = None
    lastUpdate: datetime
    url: AnyUrl

class TokenInfo(BaseLibraryModel):
    name: str
    ticker: str
    magnitude: int





