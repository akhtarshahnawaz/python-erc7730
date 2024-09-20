from typing import Union, Optional
from pydantic import AnyUrl
from erc7730.model.base import BaseLibraryModel
from erc7730.model.types import ContractAddress, Id
from erc7730.model.abi import ABI


class EIP712Domain(BaseLibraryModel):
    name: str
    type: str


class EIP712JsonSchema(BaseLibraryModel):
    primaryType: str
    types: dict[str, list[EIP712Domain]]


class EIP712Schema(BaseLibraryModel):
    eip712Schema: Union[AnyUrl, EIP712JsonSchema]


class Domain(BaseLibraryModel):
    name: Optional[str] = None
    version: Optional[str] = None
    chainId: Optional[int] = None
    verifyingContract: Optional[ContractAddress] = None


class EIP712(BaseLibraryModel):
    domain: Optional[Domain] = None
    schemas: Optional[list[Union[EIP712JsonSchema, AnyUrl]]] = None


class EIP712DomainBinding(BaseLibraryModel):
    eip712: EIP712


AbiJsonSchema = list[ABI]


class Contract(BaseLibraryModel):
    chainId: Optional[int] = None
    address: Optional[ContractAddress] = None
    abi: Optional[Union[AnyUrl, AbiJsonSchema]] = None


class ContractBinding(BaseLibraryModel):
    contract: Contract


class ContractContext(ContractBinding):
    id: Optional[Id] = None


class EIP712Context(EIP712DomainBinding):
    id: Optional[Id] = None
