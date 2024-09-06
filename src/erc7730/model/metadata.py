from datetime import datetime
from pydantic import AnyUrl
from typing import Optional
from erc7730.model.types import Enum
from erc7730.model.base import BaseLibraryModel
from typing import Union, Optional

class OwnerInfo(BaseLibraryModel):
    legalName: Optional[str] = None
    lastUpdate: datetime
    url: AnyUrl

class TokenInfo(BaseLibraryModel):
    name: str
    ticker: str
    magnitude: int

class Metadata(BaseLibraryModel):
    owner: Optional[str] = None
    info: Optional[OwnerInfo] = None
    token: Optional[TokenInfo] = None
    constants: Optional[list[str]] = None
    enums: Optional[Union[AnyUrl, Enum]] = None







