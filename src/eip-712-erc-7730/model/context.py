from typing import Union
from pydantic import AnyUrl
from eip-712-erc-7730.model.base import BaseLibraryModel
from eip-712-erc-7730.model.types import ContractAddress

class Context(BaseLibraryModel):
    context: Union[ContractBinding, EIP712DomainBinding]

class ContractBinding(BaseLibraryModel):    
    contract: Contract

class Contract(BaseLibraryModel):
    chainId: int
    address: ContractAddress
    abi: Union[AnyUrl, AbiJsonSchema]

class AbiJsonSchema(BaseLibraryModel):
    name: str
    inputs: list[AbiParameter]    
    

class EIP712DomainBinding(BaseLibraryModel):
    eip712: EIP712 

class EIP712(BaseLibraryModel):
    domain: Domain
    schemas: list[EIP712Schema]

class Domain(BaseLibraryModel):
    name: str
    version: str
    chainId: int
    verifyingContract: ContractAddress   

class EIP712Schema(BaseLibraryModel):
    eip712Schema: Union[AnyUrl, EIP712JsonSchema]

class EIP712JsonSchema(BaseLibraryModel):
    primaryType: str
    types: list[EIP712Domain]

class EIP712Domain(BaseLibraryModel):
    name: str
    type: str


