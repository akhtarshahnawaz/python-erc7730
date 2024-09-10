
from erc7730.common.pydantic import model_from_json_bytes
from erc7730.model.context import EIP712JsonSchema
from erc7730.model.erc7730_descriptor import ERC7730Descriptor, EIP712Context
from eip712 import EIP712BaseMapper
import requests


def to_eip712_mapper(erc7730: ERC7730Descriptor) -> EIP712BaseMapper:
    context = erc7730.context
    if (context is not None and isinstance(context, EIP712Context)):
        domain = context.eip712.domain
        if (domain is None):
            raise Exception(f"no domain defined for {context.eip712}")
        else:
            if (domain.chainId is None):
                raise Exception(f"chain id is None for {domain}")
            elif (domain.verifyingContract is None):
                raise Exception(f"verifying contract is None for {domain}")
            else:
                chain_id = domain.chainId
                contract_address = domain.verifyingContract
                display_name = ""
                if (domain.name is not None):
                    display_name = domain.name
                schema = dict[str, str]()
                schemas = context.eip712.schemas
                if(schemas is not None):
                    sch = None
                    for idx, item in enumerate(schemas):
                        if (isinstance(item, EIP712JsonSchema)): 
                            sch = item
                        else:
                            response = requests.get(item.__str__())
                            sch = model_from_json_bytes(response.content, EIP712JsonSchema)
                        for domain in sch.types["EIP712Domain"]:
                            schema[idx.__str__() + domain.name] = domain.type
                return EIP712BaseMapper(chain_id, contract_address, schema, display_name)
    else: 
        raise Exception(f"context for {erc7730} is None or is not EIP712")
    