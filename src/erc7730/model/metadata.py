from datetime import datetime
from pydantic import AnyUrl
from erc7730.model.base import BaseLibraryModel
from typing import Union, Optional, Dict


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
    constants: Optional[Dict[str, str]] = None
    enums: Optional[Union[AnyUrl, Dict[str, Dict[str, str]]]] = None
