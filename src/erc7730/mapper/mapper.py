
from pydantic import AnyUrl
from erc7730.common.pydantic import model_from_json_bytes
from erc7730.model.context import EIP712JsonSchema
from erc7730.model.erc7730_descriptor import ERC7730Descriptor, EIP712Context
from erc7730.model.display import Display, Reference, Field, StructFormats, FieldFormat, Fields
from eip712 import EIP712DAppDescriptor, EIP712ContractDescriptor, EIP712Mapper, EIP712MessageDescriptor, EIP712Field, EIP712Format
import requests


def to_eip712_mapper(erc7730: ERC7730Descriptor) -> EIP712DAppDescriptor|list[Exception]:
    exceptions = list[Exception]()
    context = erc7730.context
    if (context is not None and isinstance(context, EIP712Context)):
        domain = context.eip712.domain
        if (domain is None):
            exceptions.append(Exception(f"no domain defined for {context.eip712}")) # type: ignore
        else:
            if (domain.chainId is None):
                exceptions.append(Exception(f"chain id is None for {domain}")) # type: ignore
            elif (domain.verifyingContract is None):
                exceptions.append(Exception(f"verifying contract is None for {domain}")) # type: ignore
            else:
                schema = dict[str, str]()
                schs = context.eip712.schemas
                if schs is not None:
                    for item in schs:
                        sch = None
                        if (isinstance(item, EIP712JsonSchema)): 
                            sch = item
                        else:
                            try:
                                response = requests.get(item.__str__())
                                sch = model_from_json_bytes(response.content, model = EIP712JsonSchema)
                            except Exception as e:
                                exceptions.append(e) # type: ignore
                        if sch is not None:
                            for key in sch.types:
                                    for d in sch.types[key]:
                                        schema[key + "." + d.name] = d.type 
                chain_id = domain.chainId
                contract_address = domain.verifyingContract
                name = ""
                if (domain.name is not None):
                    name = domain.name
                display = erc7730.display
                contracts = list[EIP712ContractDescriptor]()
                if display is not None:
                    for primaryType in display.formats:
                        format = display.formats[primaryType]
                        messages = list[EIP712MessageDescriptor]()
                        if format.fields is not None:
                            eip712Fields = parseFields(display, primaryType, list[EIP712Field](), format.fields)
                            messages.append(EIP712MessageDescriptor(schema = schema, mapper = EIP712Mapper(label = primaryType, fields = eip712Fields)))
                        contracts.append(EIP712ContractDescriptor(address=contract_address, contractName=name, messages=messages))
                return EIP712DAppDescriptor(blockchainName="ethereum", chainId=chain_id, name=name, contracts=contracts)       
    else: 
        exceptions.append(Exception(f"context for {erc7730} is None or is not EIP712")) # type: ignore
    return exceptions

def parseFields(display: Display, primaryType: str, output: list[EIP712Field], fields: Fields) -> list[EIP712Field]:
    for _, field in fields:
         if isinstance(field, Reference):
                       # get field from definition section
            if display.definitions is not None:
                for _, f in display.definitions[field.ref]:
                    parseField(primaryType, output, f)
         elif isinstance(field, StructFormats):
            parseFields(display, primaryType, output, field.fields) 
         elif isinstance(field, Field):
            parseField(primaryType, output, field)
    return output

def parseField(primaryType: str, output: list[EIP712Field], field: Field) -> list[EIP712Field]:
    name = field.label
    assetPath = None
    fieldFormat = None
    match field.format:
        case FieldFormat.NFT_NAME:
            assetPath = field.collectionPath
        case FieldFormat.TOKEN_NAME:
            if (field.tokenAmountParameters is not None):
                assetPath = field.tokenAmountParameters.tokenPath
            fieldFormat = EIP712Format.AMOUNT
        case FieldFormat.ALLOWANCE_AMOUNT:
            if field.allowanceAmountParameters is not None:
                assetPath = field.allowanceAmountParameters.tokenPath
            fieldFormat = EIP712Format.AMOUNT
        case FieldFormat.DATE:
            fieldFormat = EIP712Format.DATETIME
        case _:
            pass                           
    output.append(EIP712Field(path=primaryType, label=name, assetPath=assetPath, format=fieldFormat, coinRef=None))
    return output
   
