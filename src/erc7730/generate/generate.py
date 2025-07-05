import os
from collections.abc import Generator
from pathlib import Path
from typing import Any, assert_never

from caseswitcher import to_title
from pydantic import TypeAdapter
from pydantic_string_url import HttpUrl

from erc7730.common.abi import ABIDataType, compute_signature, get_functions
from erc7730.common.client import get_contract_abis, get_contract_data, SourcifyContractData, extract_main_contract_source, extract_function_and_constants
from erc7730.generate.schema_tree import (
    SchemaArray,
    SchemaLeaf,
    SchemaStruct,
    SchemaTree,
    abi_function_to_tree,
    eip712_schema_to_tree,
)
from erc7730.model.abi import ABI
from erc7730.model.context import EIP712Schema
from erc7730.model.display import AddressNameType, DateEncoding, FieldFormat
from erc7730.model.input.context import (
    InputContract,
    InputContractContext,
    InputDeployment,
    InputEIP712,
    InputEIP712Context,
)
from erc7730.model.input.descriptor import InputERC7730Descriptor
from erc7730.model.input.display import (
    InputAddressNameParameters,
    InputDateParameters,
    InputDisplay,
    InputField,
    InputFieldDescription,
    InputFieldParameters,
    InputFormat,
    InputNestedFields,
)
from erc7730.model.input.metadata import InputMetadata
from erc7730.model.metadata import OwnerInfo
from erc7730.model.paths import ROOT_DATA_PATH, Array, ArrayElement, ArraySlice, DataPath, Field
from erc7730.model.paths.path_ops import data_path_append
from erc7730.model.types import Address


def generate_descriptor(
    chain_id: int,
    contract_address: Address,
    abi: str | bytes | None = None,
    eip712_schema: str | bytes | None = None,
    owner: str | None = None,
    legal_name: str | None = None,
    url: HttpUrl | None = None,
    auto: bool = False,
    local_artifact_json: str | None = None,
    local_source_path: Path | None = None,
) -> InputERC7730Descriptor:
    """
    Generate an ERC-7730 descriptor.

    If an EIP-712 schema is provided, an EIP-712 descriptor is generated for this schema, otherwise a calldata
    descriptor. If no ABI is supplied, the ABIs are fetched from Etherscan using the chain id / contract address.

    :param chain_id: contract chain id
    :param contract_address: contract address
    :param abi: JSON ABI string or buffer representation (to generate a calldata descriptor)
    :param eip712_schema: JSON EIP-712 schema string or buffer representation (to generate an EIP-712 descriptor)
    :param owner: the display name of the owner or target of the contract / message to be clear signed
    :param legal_name: the full legal name of the owner if different from the owner field
    :param url: URL with more info on the entity the user interacts with
    :return: a generated ERC-7730 descriptor
    """

    context, trees, functions = _generate_context(chain_id, contract_address, abi, eip712_schema, auto)
    
    # Get contract data for metadata inference if in auto mode
    contract_data = None
    if auto:
        if local_artifact_json is not None:
            # Create mock contract data from local artifact
            contract_data = _create_mock_contract_data(local_artifact_json, local_source_path)
        elif chain_id is not None and contract_address is not None:
            try:
                contract_data = get_contract_data(chain_id, contract_address)
            except Exception as e:
                print(f"Warning: Failed to fetch contract data for metadata inference: {e}")
    
    metadata = _generate_metadata(legal_name, owner, url, contract_data)
    display = _generate_display(trees, auto, chain_id, contract_address if auto else None, functions, metadata)

    return InputERC7730Descriptor(context=context, metadata=metadata, display=display)


def _generate_metadata(owner: str | None, legal_name: str | None, url: HttpUrl | None, contract_data: SourcifyContractData | None = None) -> InputMetadata:
    # Use provided values if available, otherwise try to infer from contract data
    inferred_owner = owner
    inferred_legal_name = legal_name
    inferred_url = url
    
    # If no explicit values provided and contract data is available, try to infer
    if contract_data is not None:
        if inferred_owner is None:
            inferred_owner = _infer_owner_from_contract_data(contract_data)
        
        if inferred_legal_name is None:
            inferred_legal_name = _infer_legal_name_from_contract_data(contract_data)
        
        if inferred_url is None:
            inferred_url = _infer_url_from_contract_data(contract_data)
    
    # Create info object if we have either legal name or URL
    info = None
    if inferred_legal_name is not None or inferred_url is not None:
        info = OwnerInfo(legalName=inferred_legal_name, url=inferred_url)
    
    # Generate constants from contract data if available
    constants = _generate_constants_from_contract_data(contract_data) if contract_data else None
    
    return InputMetadata(owner=inferred_owner, info=info, constants=constants)


def _generate_context(
    chain_id: int, contract_address: Address, abi: str | bytes | None, eip712_schema: str | bytes | None, auto: bool
) -> tuple[InputContractContext | InputEIP712Context, dict[str, SchemaTree], list | None]:
    if eip712_schema is not None:
        context, trees = _generate_context_eip712(chain_id, contract_address, eip712_schema)
        return context, trees, None
    return _generate_context_calldata(chain_id, contract_address, abi)


def _generate_context_eip712(
    chain_id: int, contract_address: Address, eip712_schema: str | bytes
) -> tuple[InputEIP712Context, dict[str, SchemaTree]]:
    schemas = TypeAdapter(list[EIP712Schema]).validate_json(eip712_schema)

    context = InputEIP712Context(
        eip712=InputEIP712(schemas=schemas, deployments=[InputDeployment(chainId=chain_id, address=contract_address)])
    )

    trees = {schema.primaryType: eip712_schema_to_tree(schema) for schema in schemas}

    return context, trees


def _generate_context_calldata(
    chain_id: int, contract_address: Address, abi: str | bytes | None
) -> tuple[InputContractContext, dict[str, SchemaTree], list]:
    if abi is not None:
        abis = TypeAdapter(list[ABI]).validate_json(abi)

    elif (abis := get_contract_abis(chain_id, contract_address)) is None:
        raise Exception("Failed to fetch contract ABIs")

    functions = list(get_functions(abis).functions.values())
    
    # Filter out view/pure functions as they won't be signed by users
    functions = [func for func in functions if func.stateMutability not in ["view", "pure"]]

    context = InputContractContext(
        contract=InputContract(abi=functions, deployments=[InputDeployment(chainId=chain_id, address=contract_address)])
    )

    trees = {compute_signature(function): abi_function_to_tree(function) for function in functions}

    return context, trees, functions


def _generate_display(trees: dict[str, SchemaTree], auto: bool = False, chain_id: int | None = None, contract_address: Address | None = None, functions: list | None = None, metadata: InputMetadata | None = None) -> InputDisplay:
    return InputDisplay(formats=_generate_formats(trees, auto, chain_id, contract_address, functions, metadata))


def _generate_formats(trees: dict[str, SchemaTree], auto: bool = False, chain_id: int | None = None, contract_address: Address | None = None, functions: list | None = None, metadata: InputMetadata | None = None) -> dict[str, InputFormat]:
    formats: dict[str, InputFormat] = {}
    
    # Initialize LLM inference if auto mode is enabled
    llm_inference = None
    contract_data = None
    function_map = {}
    
    if auto and chain_id is not None and contract_address is not None:
        try:
            from erc7730.generate.llm_inference import LLMInference
            llm_inference = LLMInference()
            contract_data = get_contract_data(chain_id, contract_address)
            
            # Create a mapping from function signature to function for LLM inference
            if functions:
                function_map = {compute_signature(func): func for func in functions}
        except Exception as e:
            print(f"Warning: Failed to initialize LLM inference: {e}")
    
    for name, tree in trees.items():
        current_function = function_map.get(name) if function_map else None
        if fields := list(_generate_fields(schema=tree, path=ROOT_DATA_PATH, auto=auto, llm_inference=llm_inference, contract_data=contract_data, function_data=current_function, metadata=metadata)):
            # Check if LLM suggested an intent message
            intent = None
            if auto and llm_inference and current_function:
                intent = llm_inference.get_function_intent(current_function)
            
            formats[name] = InputFormat(fields=fields, intent=intent)
    return formats


def _generate_fields(schema: SchemaTree, path: DataPath, auto: bool = False, llm_inference=None, contract_data=None, function_data=None, metadata=None) -> Generator[InputField, Any, Any]:
    match schema:
        case SchemaStruct(components=components) if path == ROOT_DATA_PATH:
            for name, component in components.items():
                if name:
                    yield from _generate_fields(component, data_path_append(path, Field(identifier=name)), auto, llm_inference, contract_data, function_data, metadata)

        case SchemaStruct(components=components):
            fields = [
                field
                for name, component in components.items()
                for field in _generate_fields(component, DataPath(absolute=False, elements=[Field(identifier=name)]), auto, llm_inference, contract_data, function_data, metadata)
                if name
            ]
            yield InputNestedFields(path=path, fields=fields)

        case SchemaArray(component=component):
            match component:
                case SchemaStruct() | SchemaArray():
                    yield InputNestedFields(
                        path=data_path_append(path, Array()),
                        fields=list(_generate_fields(component, DataPath(absolute=False, elements=[]), auto, llm_inference, contract_data, function_data, metadata)),
                    )
                case SchemaLeaf():
                    yield from _generate_fields(component, data_path_append(path, Array()), auto, llm_inference, contract_data, function_data, metadata)
                case _:
                    assert_never(schema)

        case SchemaLeaf(data_type=data_type):
            name = _get_leaf_name(path)
            # Extract original parameter name from path for LLM lookup
            param_name = _get_param_name(path)
            format, params = _generate_field(name, param_name, data_type, auto, llm_inference, contract_data, function_data, metadata)
            
            # Check if LLM suggested a better label
            label = name
            if auto and llm_inference and function_data:
                suggested_label = llm_inference.get_field_label(function_data, param_name)
                if suggested_label:
                    label = suggested_label
            
            yield InputFieldDescription(path=path, label=label, format=format, params=params)

        case _:
            assert_never(schema)


def _generate_field(name: str, param_name: str, data_type: ABIDataType, auto: bool = False, llm_inference=None, contract_data=None, function_data=None, metadata=None) -> tuple[FieldFormat, InputFieldParameters | None]:
    # Try LLM inference first if available and auto mode is enabled
    if auto and llm_inference and function_data:
        try:
            llm_formats = llm_inference.infer_field_formats(function_data, contract_data, metadata)
            # Check both parameter name and display name
            if param_name in llm_formats:
                return llm_formats[param_name]
            elif name in llm_formats:
                return llm_formats[name]
        except Exception as e:
            print(f"Warning: LLM inference failed for field {name}: {e}")
    
    # Fallback to heuristic-based inference
    match data_type:
        case ABIDataType.UINT | ABIDataType.INT:
            # other applicable formats could be TOKEN_AMOUNT, UNIT or ENUM, but we can't tell

            if _contains_any_of(name, "duration"):
                return FieldFormat.DURATION, None

            if _contains_any_of(name, "height"):
                return FieldFormat.DATE, InputDateParameters(encoding=DateEncoding.BLOCKHEIGHT)

            if _contains_any_of(name, "deadline", "expiration", "until", "time", "timestamp"):
                return FieldFormat.DATE, InputDateParameters(encoding=DateEncoding.TIMESTAMP)

            if _contains_any_of(name, "amount", "value", "price"):
                return FieldFormat.AMOUNT, None

            return FieldFormat.RAW, None

        case ABIDataType.UFIXED | ABIDataType.FIXED:
            return FieldFormat.RAW, None

        case ABIDataType.ADDRESS:
            if _contains_any_of(name, "collection", "nft"):
                return FieldFormat.NFT_NAME, InputAddressNameParameters(types=[AddressNameType.COLLECTION])

            if _contains_any_of(name, "spender"):
                return FieldFormat.ADDRESS_NAME, InputAddressNameParameters(types=[AddressNameType.CONTRACT])

            if _contains_any_of(name, "asset", "token"):
                return FieldFormat.ADDRESS_NAME, InputAddressNameParameters(types=[AddressNameType.TOKEN])

            if _contains_any_of(name, "from", "to", "owner", "recipient", "receiver", "account"):
                return FieldFormat.ADDRESS_NAME, InputAddressNameParameters(
                    types=[AddressNameType.EOA, AddressNameType.WALLET]
                )

            return FieldFormat.ADDRESS_NAME, InputAddressNameParameters(types=list(AddressNameType))

        case ABIDataType.BOOL:
            return FieldFormat.RAW, None

        case ABIDataType.BYTES:
            if _contains_any_of(name, "calldata"):
                return FieldFormat.CALL_DATA, None

            return FieldFormat.RAW, None

        case ABIDataType.STRING:
            return FieldFormat.RAW, None

        case _:
            assert_never(data_type)


def _get_leaf_name(path: DataPath) -> str:
    for element in reversed(path.elements):
        match element:
            case Field(identifier=name):
                return to_title(name).strip()
            case Array() | ArrayElement() | ArraySlice():
                continue
            case _:
                assert_never(element)
    return "unknown"


def _get_param_name(path: DataPath) -> str:
    """Extract the original parameter name from the path (without title case conversion)."""
    for element in reversed(path.elements):
        match element:
            case Field(identifier=name):
                return name or "unknown"
            case Array() | ArrayElement() | ArraySlice():
                continue
            case _:
                assert_never(element)
    return "unknown"


def _contains_any_of(name: str, *values: str) -> bool:
    name_lower = name.lower()
    return any(value in name_lower for value in values)


def _infer_owner_from_contract_data(contract_data: SourcifyContractData) -> str | None:
    """Infer the owner/project name from contract data."""
    if contract_data.metadata is None:
        return None
    
    # Try to get contract name from compilation target
    compilation_target = contract_data.metadata.get("settings", {}).get("compilationTarget", {})
    if compilation_target:
        return next(iter(compilation_target.values()), None)
    
    # Try to extract from devdoc title
    devdoc = contract_data.devdoc
    if devdoc and "title" in devdoc:
        title = devdoc["title"]
        # Extract the main entity name from title
        # E.g., "Uniswap V3 Pool" -> "Uniswap"
        words = title.split()
        if words:
            return words[0]
    
    # Try to extract from devdoc author
    if devdoc and "author" in devdoc:
        author = devdoc["author"]
        # Extract the first part of author info
        if " - " in author:
            return author.split(" - ")[0].strip()
        elif ":" in author:
            return author.split(":")[0].strip()
    
    return None


def _infer_legal_name_from_contract_data(contract_data: SourcifyContractData) -> str | None:
    """Infer the legal name from contract data."""
    if contract_data.metadata is None:
        return None

    # Try to extract from devdoc title if it looks like a full legal name
    devdoc = contract_data.devdoc
    if devdoc and "title" in devdoc:
        title = devdoc["title"]
        # If title contains "Protocol", "DAO", "Limited", etc., it might be a legal name
        legal_indicators = ["Protocol", "DAO", "Limited", "Inc", "Corp", "Foundation"]
        if any(indicator in title for indicator in legal_indicators):
            return title
    
    return None


def _infer_url_from_contract_data(contract_data: SourcifyContractData) -> HttpUrl | None:
    """Infer the URL from contract data."""
    if contract_data.metadata is None:
        return None
    
    # Look for URLs in devdoc details or other fields
    devdoc = contract_data.devdoc
    if devdoc and "details" in devdoc:
        details = devdoc["details"]
        # Basic URL extraction - look for common patterns
        import re
        url_pattern = r'https?://[^\s<>"{\[\]|\\^`]+'
        urls = re.findall(url_pattern, details)
        if urls:
            try:
                return HttpUrl(urls[0])
            except Exception:
                pass
    
    return None


def _generate_constants_from_contract_data(contract_data: SourcifyContractData) -> dict[str, str | int | bool | float | None] | None:
    """Generate constants from contract data by extracting contract constants/state variables."""
    if not contract_data.sources:
        return None
    
    constants = {}
    
    # Extract constants from the main contract source
    try:
        main_contract_source = extract_main_contract_source(contract_data)
        if main_contract_source:
            # Extract constants globally from the contract source
            # Use any function name to get contract-level constants
            from erc7730.common.abi import get_functions
            
            functions_obj = get_functions(contract_data.abi)
            if functions_obj.functions:
                # Get the first function to extract contract-level constants
                first_func = next(iter(functions_obj.functions.values()))
                try:
                    _, constants_code = extract_function_and_constants(main_contract_source, first_func.name or "")
                    if constants_code:
                        # Parse constants from the extracted code
                        parsed_constants = _parse_constants_from_code(constants_code)
                        constants.update(parsed_constants)
                        
                        # Debug logging
                        if constants and os.environ.get("DEBUG") == "1":
                            print(f"Extracted {len(constants)} constants from contract: {list(constants.keys())}")
                except Exception as e:
                    print(f"Warning: Failed to extract constants from contract source: {e}")
    except Exception as e:
        print(f"Warning: Failed to extract constants from contract data: {e}")
    
    return constants if constants else None


def _parse_constants_from_code(constants_code: str) -> dict[str, str | int | bool | float | None]:
    """Parse constants from Solidity code."""
    import re
    
    constants = {}
    
    # Debug logging
    if os.environ.get("DEBUG") == "1":
        print("Parsing constants from code:")
        print(constants_code)
        print("---")
    
    lines = constants_code.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
            continue
            
        # Look for constant declarations - more flexible pattern
        if 'constant' in stripped and '=' in stripped:
            # Pattern for constant declarations - handles various visibility modifiers
            patterns = [
                r'(\w+)\s+(?:public\s+|private\s+|internal\s+)?constant\s+(\w+)\s*=\s*([^;]+)',
                r'(\w+)\s+constant\s+(?:public\s+|private\s+|internal\s+)?(\w+)\s*=\s*([^;]+)',
                r'constant\s+(\w+)\s+(\w+)\s*=\s*([^;]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, stripped)
                if match:
                    if len(match.groups()) == 3:
                        data_type, name, value = match.groups()
                        parsed_value = _parse_constant_value(value.strip(), data_type)
                        if parsed_value is not None:
                            constants[name] = parsed_value
                            if os.environ.get("DEBUG") == "1":
                                print(f"Found constant: {name} = {parsed_value}")
                    break
                    
        # Look for immutable variables
        elif 'immutable' in stripped:
            # Pattern for immutable declarations
            pattern = r'(\w+)\s+(?:public\s+|private\s+|internal\s+)?immutable\s+(\w+)'
            match = re.search(pattern, stripped)
            if match:
                data_type, name = match.groups()
                # For immutable variables, we can't determine the value from source
                # but we can note their existence for potential reference
                constants[name] = None
                if os.environ.get("DEBUG") == "1":
                    print(f"Found immutable: {name} (value unknown)")
    
    return constants


def _parse_constant_value(value: str, data_type: str) -> str | int | bool | float | None:
    """Parse a constant value from Solidity code."""
    value = value.strip()
    
    # Remove trailing semicolon if present
    if value.endswith(';'):
        value = value[:-1]
    
    # Boolean values
    if value.lower() in ['true', 'false']:
        return value.lower() == 'true'
    
    # String values
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]  # Remove quotes
    
    # Hex values
    if value.startswith('0x'):
        return value  # Keep as hex string
    
    # Numeric values
    try:
        # Try integer first
        if '.' not in value and 'e' not in value.lower():
            return int(value)
        else:
            return float(value)
    except ValueError:
        pass
    
    # Return as string if we can't parse it
    return value


def _create_mock_contract_data(artifact_json: str, source_path: Path | None) -> SourcifyContractData:
    """Create a mock SourcifyContractData from local artifact and source file."""
    import json
    
    try:
        artifact_data = json.loads(artifact_json)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid artifact JSON: {e}")
        return SourcifyContractData(abi=None, sources=None)
    
    # Extract ABI
    abi = artifact_data.get("abi", [])
    
    # Extract metadata if available
    metadata = artifact_data.get("metadata")
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = None
    
    # Extract userdoc and devdoc if available
    userdoc = artifact_data.get("userdoc")
    devdoc = artifact_data.get("devdoc")
    
    # Create sources dict if source file is provided
    sources = None
    if source_path and source_path.exists():
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                source_content = f.read()
            
            # Extract contract name from artifact
            contract_name = artifact_data.get("contractName", "Contract")
            
            sources = {
                str(source_path): {
                    "content": source_content
                }
            }
            
            # If metadata has sources, use that structure instead
            if metadata and "sources" in metadata:
                sources = {}
                for source_file, source_info in metadata["sources"].items():
                    if source_file == str(source_path) or source_file.endswith(source_path.name):
                        sources[source_file] = {
                            "content": source_content
                        }
                        break
                else:
                    # Fallback: use the source path as key
                    sources[str(source_path)] = {
                        "content": source_content
                    }
        except Exception as e:
            print(f"Warning: Could not read source file {source_path}: {e}")
    
    return SourcifyContractData(
        abi=abi,
        metadata=metadata,
        userdoc=userdoc,
        devdoc=devdoc,
        sources=sources
    )
