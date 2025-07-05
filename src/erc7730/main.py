import json
import logging
import os
from pathlib import Path
from typing import Annotated, assert_never

import dotenv

from eip712.convert.input_to_resolved import EIP712InputToResolvedConverter
from eip712.model.input.descriptor import InputEIP712DAppDescriptor
from pydantic import RootModel
from pydantic_string_url import HttpUrl
from rich import print
from typer import Argument, Exit, Option, Typer

from erc7730.common.output import ConsoleOutputAdder
from erc7730.convert.calldata.convert_erc7730_input_to_calldata import erc7730_descriptor_to_calldata_descriptors
from erc7730.convert.convert import convert_to_file_and_print_errors
from erc7730.convert.ledger.eip712.convert_eip712_to_erc7730 import EIP712toERC7730Converter
from erc7730.convert.ledger.eip712.convert_erc7730_to_eip712 import ERC7730toEIP712Converter
from erc7730.convert.resolved.convert_erc7730_input_to_resolved import ERC7730InputToResolved
from erc7730.format.format import format_all_and_print_errors
from erc7730.generate.generate import generate_descriptor
from erc7730.lint.lint import lint_all_and_print_errors
from erc7730.list.list import list_all
from erc7730.model import ERC7730ModelType
from erc7730.model.base import Model
from erc7730.model.calldata.descriptor import CalldataDescriptor
from erc7730.model.input.descriptor import InputERC7730Descriptor
from erc7730.model.resolved.descriptor import ResolvedERC7730Descriptor
from erc7730.model.types import Address

dotenv.load_dotenv()

if os.environ.get("DEBUG", "0") == "1":
    logging.basicConfig(
        format="%(levelname)s [%(asctime)s] %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG
    )


app = Typer(
    name="erc7730",
    no_args_is_help=True,
    help="""
    ERC-7730 tool.
    """,
)
convert_app = Typer(
    name="convert",
    no_args_is_help=True,
    short_help="Commands to convert descriptor files.",
    help="""
    Commands to convert descriptor files.
    """,
)
app.add_typer(convert_app)


@app.command(
    name="schema",
    short_help="Print ERC-7730 descriptor JSON schema.",
    help="""
    Print ERC-7730 descriptor JSON schema.
    """,
)
def command_schema(
    model_type: Annotated[ERC7730ModelType, Argument(help="The descriptor form ")] = ERC7730ModelType.INPUT,
) -> None:
    descriptor_type: type[Model]
    match model_type:
        case ERC7730ModelType.INPUT:
            descriptor_type = InputERC7730Descriptor
        case ERC7730ModelType.RESOLVED:
            descriptor_type = ResolvedERC7730Descriptor
        case _:
            assert_never(model_type)

    print(json.dumps(descriptor_type.model_json_schema(by_alias=True), indent=4))


@app.command(
    name="lint",
    short_help="Validate descriptor files.",
    help="""
    Validate descriptor files.
    """,
)
def command_lint(
    paths: Annotated[list[Path], Argument(help="The files or directory paths to lint")],
    gha: Annotated[bool, Option(help="Enable Github annotations output")] = False,
) -> None:
    if not lint_all_and_print_errors(paths, gha):
        raise Exit(1)


@app.command(
    name="list",
    short_help="List descriptor files.",
    help="""
    Recursively list all descriptor files, starting from current directory by default.
    """,
)
def command_list(
    paths: Annotated[list[Path] | None, Argument(help="The files or directory paths to search")] = None,
) -> None:
    if not list_all(paths or [Path.cwd()]):
        raise Exit(1)


@app.command(
    name="format",
    short_help="Format descriptor files.",
    help="""
    Recursively find and format all descriptor files, starting from current directory by default.
    """,
)
def command_format(
    paths: Annotated[list[Path] | None, Argument(help="The files or directory paths to search")] = None,
) -> None:
    if not format_all_and_print_errors(paths or [Path.cwd()]):
        raise Exit(1)


@app.command(
    name="resolve",
    short_help="Convert descriptor to resolved form.",
    help="""
    Convert descriptor to resolved form:
        - URLs fetched
        - Contract addresses normalized to lowercase
        - References inlined
        - Constants inlined
        - Field definitions inlined
        - Nested fields flattened where possible
        - Selectors converted to 4 bytes form
    
    See `erc7730 schema resolved` for the resolved descriptor schema.
    """,
)
def command_resolve(
    input_path: Annotated[Path, Argument(help="The input ERC-7730 file path")],
) -> None:
    input_descriptor = InputERC7730Descriptor.load(input_path)
    if (resolved_descriptor := ERC7730InputToResolved().convert(input_descriptor, ConsoleOutputAdder())) is None:
        raise Exit(1)
    print(resolved_descriptor.to_json_string())


@app.command(
    name="generate",
    short_help="Bootstrap a descriptor for given ABI/schema.",
    help="""
    Fetches ABI or schema files and generates a minimal descriptor.
    """,
)
def command_generate(
    chain_id: Annotated[int | None, Option(help="The EIP-155 chain id")] = None,
    address: Annotated[Address | None, Option(help="The contract address")] = None,
    abi: Annotated[Path | None, Option(help="Path to a JSON ABI file (to generate a calldata descriptor)")] = None,
    schema: Annotated[Path | None, Option(help="Path to an EIP-712 schema (to generate an EIP-712 descriptor)")] = None,
    owner: Annotated[str | None, Option(help="The display name of the owner or target of the contract")] = None,
    legal_name: Annotated[str | None, Option(help="The full legal name of the owner")] = None,
    url: Annotated[str | None, Option(help="URL with more info on the entity interacted with")] = None,
    auto: Annotated[bool, Option(help="Enable LLM-based automatic inference for generating display formats")] = False,
    local: Annotated[bool, Option(help="Use local artifact data from environment variables (set by Hardhat plugin)")] = False,
    output: Annotated[Path | None, Option(help="Output file path for the generated ERC-7730 descriptor")] = None,
) -> None:
    if schema is not None and abi is not None:
        print("Cannot specify both ABI and schema.")
        raise Exit(1)
    
    if local and (abi is not None or schema is not None):
        print("Cannot specify both --local and --abi/--schema.")
        raise Exit(1)
    
    schema_buffer = None
    abi_buffer = None
    local_artifact_json = None
    local_source_path = None

    if local:
        # Get data from environment variables set by Hardhat plugin
        env_chain_id = os.environ.get("CHAIN_ID")
        env_address = os.environ.get("DEPLOYED_CONTRACT_ADDRESS")
        env_artifact = os.environ.get("CONTRACT_ARTIFACT")
        env_source_path = os.environ.get("CONTRACT_SOURCE_PATH")
        
        if not env_chain_id:
            print("CHAIN_ID environment variable is required when using --local")
            raise Exit(1)
        if not env_address:
            print("DEPLOYED_CONTRACT_ADDRESS environment variable is required when using --local")
            raise Exit(1)
        if not env_artifact:
            print("CONTRACT_ARTIFACT environment variable is required when using --local")
            raise Exit(1)
            
        # Override command line parameters with environment variables
        chain_id = int(env_chain_id)
        address = Address(env_address)
        local_artifact_json = env_artifact
        local_source_path = Path(env_source_path) if env_source_path else None
        
        # Parse artifact JSON to extract ABI
        try:
            artifact_data = json.loads(env_artifact)
            if "abi" in artifact_data:
                abi_buffer = json.dumps(artifact_data["abi"]).encode('utf-8')
            else:
                print("No ABI found in artifact JSON from environment.")
                raise Exit(1)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in CONTRACT_ARTIFACT environment variable: {e}")
            raise Exit(1)
    else:
        # Normal mode - require chain_id and address
        if chain_id is None:
            print("--chain-id is required when not using --local")
            raise Exit(1)
        if address is None:
            print("--address is required when not using --local")
            raise Exit(1)
            
        if schema is not None:
            with open(schema, "rb") as f:
                schema_buffer = f.read()
        elif abi is not None:
            with open(abi, "rb") as f:
                abi_buffer = f.read()

    descriptor = generate_descriptor(
        chain_id=chain_id,
        contract_address=address,
        abi=abi_buffer,
        eip712_schema=schema_buffer,
        owner=owner,
        legal_name=legal_name,
        url=HttpUrl(url) if url is not None else None,
        auto=auto,
        local_artifact_json=local_artifact_json,
        local_source_path=local_source_path,
    )
    
    result_json = descriptor.to_json_string()
    
    if output is not None:
        # Write to file
        with open(output, "w", encoding="utf-8") as f:
            f.write(result_json)
        print(f"ERC-7730 descriptor generated and saved to: {output}")
    else:
        # Print to stdout
        print(result_json)


@app.command(
    name="calldata",
    short_help="Display calldata descriptors for an ERC-7730 file.",
    help="""
    Display calldata descriptor(s) for an ERC-7730 file.
    """,
)
def command_calldata(
    input_erc7730_path: Annotated[Path, Argument(help="The input ERC-7730 file path")],
    source: Annotated[str | None, Option(help="Source URL of the descriptor file")] = None,
    chain_id: Annotated[int | None, Option(help="Only emit calldata descriptors for given chain ID")] = None,
) -> None:
    input_descriptor = InputERC7730Descriptor.load(input_erc7730_path)

    model = RootModel[list[CalldataDescriptor]](
        erc7730_descriptor_to_calldata_descriptors(
            input_descriptor, source=HttpUrl(source) if source is not None else None, chain_id=chain_id
        )
    )
    print(model.model_dump_json(indent=2, exclude_none=True))


if __name__ == "__main__":
    app()


@convert_app.command(
    name="eip712-to-erc7730",
    short_help="Convert a legacy EIP-712 descriptor file to an ERC-7730 file.",
    help="""
    Convert a legacy EIP-712 descriptor file to an ERC-7730 file.
    """,
)
def command_convert_eip712_to_erc7730(
    input_eip712_path: Annotated[Path, Argument(help="The input EIP-712 file path")],
    output_erc7730_path: Annotated[Path, Argument(help="The output ERC-7730 file path")],
) -> None:
    input_descriptor = InputEIP712DAppDescriptor.load(input_eip712_path)
    resolved_descriptor = EIP712InputToResolvedConverter().convert(input_descriptor)
    if not convert_to_file_and_print_errors(
        input_descriptor=resolved_descriptor,
        output_file=output_erc7730_path,
        converter=EIP712toERC7730Converter(),
    ):
        raise Exit(1)


@convert_app.command(
    name="erc7730-to-eip712",
    short_help="Convert an ERC-7730 file to a legacy EIP-712 descriptor file.",
    help="""
    Convert an ERC-7730 file to a legacy EIP-712 descriptor file (if applicable).
    """,
)
def command_convert_erc7730_to_eip712(
    input_erc7730_path: Annotated[Path, Argument(help="The input ERC-7730 file path")],
    output_eip712_path: Annotated[Path, Argument(help="The output EIP-712 file path")],
) -> None:
    input_descriptor = InputERC7730Descriptor.load(input_erc7730_path)
    resolved_descriptor = ERC7730InputToResolved().convert(input_descriptor, ConsoleOutputAdder())
    if resolved_descriptor is None or not convert_to_file_and_print_errors(
        input_descriptor=resolved_descriptor,
        output_file=output_eip712_path,
        converter=ERC7730toEIP712Converter(),
    ):
        raise Exit(1)
