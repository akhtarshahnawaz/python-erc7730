from typing import Annotated as Ann
from pydantic import Field

ContractAddress = Ann[str, Field(min_length=0, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")]
Enum = Ann[list[str]]
