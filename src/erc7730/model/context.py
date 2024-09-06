from typing import Union, Optional
from pydantic import AnyUrl
from erc7730.model.base import BaseLibraryModel
from erc7730.model.types import ContractAddress, Id


class EIP712Domain(BaseLibraryModel):
    name: str
    type: str

class EIP712JsonSchema(BaseLibraryModel):
    primaryType: str
    types: list[EIP712Domain]

class EIP712Schema(BaseLibraryModel):
    eip712Schema: Union[AnyUrl, EIP712JsonSchema]

class Domain(BaseLibraryModel):
    name: str
    version: str
    chainId: int
    verifyingContract: ContractAddress

class EIP712(BaseLibraryModel):
    domain: Domain
    schemas: Optional[list[EIP712Schema]] = None

class EIP712DomainBinding(BaseLibraryModel):
    eip712: EIP712   

class AbiParameter(BaseLibraryModel):
    name: str
    type: str
    internalType: Optional[str] = None
    components: Optional[list[BaseLibraryModel]] = None 
    """ todo: use AbiParameter instead of BaseLibraryModel type """ 

class AbiJsonSchema(BaseLibraryModel):
    name: str
    inputs: list[AbiParameter]

class Contract(BaseLibraryModel):
    chainId: int
    address: ContractAddress
    abi: Union[AnyUrl, AbiJsonSchema]

class ContractBinding(BaseLibraryModel): 
    contract: Contract

class ContractContext(ContractBinding):
    id: Optional[Id] = None        

class EIP712Context(EIP712DomainBinding):
    id: Optional[Id] = None





    
    





 








