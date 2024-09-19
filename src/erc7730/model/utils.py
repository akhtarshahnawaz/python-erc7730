from lib2to3.fixes.fix_input import context
from typing import Type

from pydantic import AnyUrl, RootModel

from erc7730.model.context import EIP712Context, ContractContext, EIP712JsonSchema
from erc7730.model.abi import ABI
from erc7730.model.erc7730_descriptor import ERC7730Descriptor
from rich import print
import requests

def resolve_external_references(descriptor: ERC7730Descriptor) -> ERC7730Descriptor:
    if isinstance(descriptor.context, EIP712Context):
        return _resolve_external_references_eip712(descriptor)
    if isinstance(descriptor.context, ContractContext):
        return _resolve_external_references_contract(descriptor)
    raise ValueError("Invalid context type")

def _resolve_external_references_eip712(descriptor: ERC7730Descriptor) -> ERC7730Descriptor:
    schemas: list[EIP712JsonSchema | AnyUrl] = descriptor.context.eip712.schemas # type:ignore
    schemas_resolved = []
    if schemas is None:
        raise ValueError("Missing EIP-712 message schemas")
    for schema in schemas:
        if isinstance(schemas, AnyUrl):
            resp = requests.get(fix_uri(schema))  # type:ignore
            resp.raise_for_status()
            model: Type[RootModel[EIP712JsonSchema]] = RootModel[EIP712JsonSchema]
            json = resp.json()
            schema_resolved = model.model_validate(json).root
        else:
            schema_resolved = schema
        schemas_resolved.append(schema_resolved)
    return descriptor.model_copy(update={"context": descriptor.context.model_copy(update={"eip712": descriptor.context.eip712.model_copy(update={"schemas": schemas_resolved})})})

def _resolve_external_references_contract(descriptor: ERC7730Descriptor) -> ERC7730Descriptor:
    abis: Union[AnyUrl, list[ABI]] = descriptor.context.contract.abi # type:ignore
    if abis is None:
        raise ValueError("Missing contract ABI")
    if isinstance(abis, AnyUrl):
        resp = requests.get(_fix_uri(abis))  # type:ignore
        resp.raise_for_status()
        json = resp.json()
        model: Type[RootModel[list[ABI]]] = RootModel[list[ABI]]
        abis_resolved = model.model_validate(json).root
        pass
    else:
        abis_resolved = abis
    return descriptor.model_copy(update={"context": descriptor.context.model_copy(update={"contract": descriptor.context.contract.model_copy(update={"abi": abis_resolved})})})

def _fix_uri(url: AnyUrl) -> AnyUrl:
    # YOLO hackathon
    return AnyUrl(str(url).replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/"))
