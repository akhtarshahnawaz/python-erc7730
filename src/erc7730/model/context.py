from typing import ForwardRef, Union, Optional
from pydantic import AnyUrl
from erc7730.model.base import BaseLibraryModel
from erc7730.model.types import ContractAddress, Id


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
    schemas:  Optional[list[Union[EIP712JsonSchema, AnyUrl]]] = None

class EIP712DomainBinding(BaseLibraryModel):
    eip712: EIP712   

class AbiParameter(BaseLibraryModel):
    name: str
    type: str
    internalType: Optional[str] = None
    components: Optional[list[ForwardRef('AbiParameter')]] = None # type: ignore
AbiParameter.model_rebuild()
# todo: use AbiParameter instead of BaseLibraryModel type

class AbiJsonSchema(BaseLibraryModel):
    name: str
    inputs: list[AbiParameter]

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





    
    





 
