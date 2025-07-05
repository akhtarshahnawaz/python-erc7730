import json
import os
from abc import ABC
from functools import cache
from typing import Any, TypeVar, final, override

from hishel import CacheTransport, FileStorage
from httpx import URL, BaseTransport, Client, HTTPTransport, Request, Response
from httpx._content import IteratorByteStream
from httpx_file import FileTransport
from limiter import Limiter
from pydantic import ConfigDict, TypeAdapter, ValidationError
from pydantic_string_url import FileUrl, HttpUrl
from xdg_base_dirs import xdg_cache_home

from erc7730.model.abi import ABI
from erc7730.model.base import Model
from erc7730.model.types import Address

ETHERSCAN = "api.etherscan.io"
SOURCIFY = "sourcify.dev"

_T = TypeVar("_T")


class EtherscanChain(Model):
    """Etherscan supported chain info."""

    model_config = ConfigDict(strict=False, frozen=True, extra="ignore")
    chainname: str
    chainid: int
    blockexplorer: HttpUrl


class ProxyImplementation(Model):
    """Proxy implementation info."""
    
    model_config = ConfigDict(strict=False, frozen=True, extra="ignore")
    address: Address
    name: str | None = None


class ProxyResolution(Model):
    """Proxy resolution information."""
    
    model_config = ConfigDict(strict=False, frozen=True, extra="ignore")
    isProxy: bool
    proxyType: str | None = None
    implementations: list[ProxyImplementation] | None = None


class SourcifyContractData(Model):
    """Sourcify contract data response."""

    model_config = ConfigDict(strict=False, frozen=True, extra="ignore")
    abi: list[ABI] | None = None
    metadata: dict[str, Any] | None = None
    userdoc: dict[str, Any] | None = None
    devdoc: dict[str, Any] | None = None
    proxyResolution: ProxyResolution | None = None
    compilation: dict[str, Any] | None = None
    sources: dict[str, dict[str, Any]] | None = None


def extract_main_contract_source(sourcify_obj: SourcifyContractData) -> tuple[str, str, str]:
    """
    Return (file_path, contract_name, solidity_source) from a Sourcify JSON blob.

    Parameters
    ----------
    sourcify_obj : SourcifyContractData
        The parsed Sourcify verification response.

    Returns
    -------
    tuple
        path   – absolute / remapped path inside 'sources', e.g.
                 '@aave/core-v3/contracts/…/InitializableImmutableAdminUpgradeabilityProxy.sol'
        cname  – the contract name, e.g. 'InitializableImmutableAdminUpgradeabilityProxy'
        source – the full Solidity code (string).
    
    Raises
    ------
    ValueError
        If compilation data or sources are not available, or if the contract path is not found.
    """
    # Check if we have compilation data
    if not sourcify_obj.compilation or not sourcify_obj.sources:
        raise ValueError("Compilation data or sources not available in Sourcify response")
    
    # 1) Fully-qualified name is "path:ContractName"
    fq_name = sourcify_obj.compilation.get("fullyQualifiedName")
    if not fq_name:
        raise ValueError("fullyQualifiedName not found in compilation data")
    
    if ":" not in fq_name:
        raise ValueError(f"Invalid fullyQualifiedName format: {fq_name}")
    
    path, cname = fq_name.split(":", 1)

    # 2) Look the path up in the 'sources' dict
    try:
        source_info = sourcify_obj.sources[path]
        source_code = source_info.get("content")
        if not source_code:
            raise ValueError(f"Source content not found for path {path}")
    except KeyError as e:
        raise ValueError(f"Path {path} not found in sources") from e

    return path, cname, source_code


@cache
def get_supported_chains() -> list[EtherscanChain]:
    """
    Get supported chains from Etherscan.

    :return: Etherscan supported chains, with name/chain id/block explorer URL
    """
    return get(url=HttpUrl(f"https://{ETHERSCAN}/v2/chainlist"), model=list[EtherscanChain])


def get_contract_abis(chain_id: int, contract_address: Address) -> list[ABI]:
    """
    Get contract ABIs from Sourcify, merging proxy and implementation ABIs when applicable.

    :param chain_id: EIP-155 chain ID
    :param contract_address: EVM contract address
    :return: deserialized list of ABIs (merged if proxy)
    :raises Exception: if contract not found or not verified on Sourcify
    """
    try:
        contract_data = get(
            url=HttpUrl(f"https://{SOURCIFY}/server/v2/contract/{chain_id}/{contract_address}"),
            fields="abi,metadata,userdoc,devdoc,proxyResolution,compilation,sources",
            model=SourcifyContractData,
        )
        
        proxy_abi = contract_data.abi or []
        
        # If this is a proxy and we have implementation info, merge ABIs
        if (contract_data.proxyResolution and 
            contract_data.proxyResolution.isProxy and 
            contract_data.proxyResolution.implementations):
            
            # Try to get ABI from the first implementation
            impl_address = contract_data.proxyResolution.implementations[0].address
            try:
                impl_contract_data = get(
                    url=HttpUrl(f"https://{SOURCIFY}/server/v2/contract/{chain_id}/{impl_address}"),
                    fields="abi,metadata,userdoc,devdoc,compilation,sources",
                    model=SourcifyContractData,
                )
                if impl_contract_data.abi is not None:
                    # Merge proxy ABI and implementation ABI
                    # Implementation ABI first, then proxy-specific functions
                    merged_abi = list(impl_contract_data.abi)
                    
                    # Add proxy-specific functions that aren't in implementation
                    impl_function_names = {abi.name for abi in impl_contract_data.abi if hasattr(abi, 'name') and abi.name}
                    for proxy_function in proxy_abi:
                        if (hasattr(proxy_function, 'name') and 
                            proxy_function.name and 
                            proxy_function.name not in impl_function_names):
                            merged_abi.append(proxy_function)
                    
                    print(f"Merged proxy and implementation ABIs: {len(proxy_abi)} proxy + {len(impl_contract_data.abi)} implementation = {len(merged_abi)} total functions")
                    return merged_abi
            except Exception as impl_e:
                print(f"Warning: Could not fetch implementation ABI from {impl_address}: {impl_e}")
        
        # Fallback to proxy ABI if available
        if not proxy_abi:
            raise Exception("ABI not available for this contract on Sourcify")
        return proxy_abi
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            raise Exception(f"contract not found on Sourcify for chain {chain_id}") from e
        raise e


def get_contract_data(chain_id: int, contract_address: Address) -> SourcifyContractData:
    """
    Get full contract data from Sourcify including ABI, metadata, userdoc, devdoc, and proxy resolution.

    :param chain_id: EIP-155 chain ID
    :param contract_address: EVM contract address
    :return: SourcifyContractData containing all available contract information
    :raises Exception: if contract not found or not verified on Sourcify
    """
    try:
        contract_data = get(
            url=HttpUrl(f"https://{SOURCIFY}/server/v2/contract/{chain_id}/{contract_address}"),
            fields="abi,metadata,userdoc,devdoc,proxyResolution,compilation,sources",
            model=SourcifyContractData,
        )
        
        # If this is a proxy and we have implementation info, merge implementation data
        if (contract_data.proxyResolution and 
            contract_data.proxyResolution.isProxy and 
            contract_data.proxyResolution.implementations):
            
            # Try to get data from the first implementation
            impl_address = contract_data.proxyResolution.implementations[0].address
            try:
                impl_contract_data = get(
                    url=HttpUrl(f"https://{SOURCIFY}/server/v2/contract/{chain_id}/{impl_address}"),
                    fields="abi,metadata,userdoc,devdoc,compilation,sources",
                    model=SourcifyContractData,
                )
                
                # Merge implementation data with proxy data, preferring implementation data
                merged_data = {
                    "abi": impl_contract_data.abi or contract_data.abi,
                    "metadata": impl_contract_data.metadata or contract_data.metadata,
                    "userdoc": impl_contract_data.userdoc or contract_data.userdoc,
                    "devdoc": impl_contract_data.devdoc or contract_data.devdoc,
                    "proxyResolution": contract_data.proxyResolution,
                }
                
                print(f"Merged implementation data from {impl_address} for proxy at {contract_address}")
                return SourcifyContractData(**merged_data)
                
            except Exception as impl_e:
                print(f"Warning: Could not fetch implementation data from {impl_address}: {impl_e}")
        
        return contract_data
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            raise Exception(f"contract not found on Sourcify for chain {chain_id}") from e
        raise e


def get_contract_explorer_url(chain_id: int, contract_address: Address) -> HttpUrl:
    """
    Get contract explorer site URL (for opening in a browser).

    :param chain_id: EIP-155 chain ID
    :param contract_address: EVM contract address
    :return: URL to the contract explorer site
    :raises NotImplementedError: if chain id not supported
    """
    for chain in get_supported_chains():
        if chain.chainid == chain_id:
            return HttpUrl(f"{chain.blockexplorer}/address/{contract_address}#code")
    raise NotImplementedError(
        f"Chain ID {chain_id} is not supported, please report this to authors of python-erc7730 library"
    )


def get(model: type[_T], url: HttpUrl | FileUrl, **params: Any) -> _T:
    """
    Fetch data from a file or an HTTP URL and deserialize it.

    This method implements some automated adaptations to handle user provided URLs:
     - GitHub: adaptation to "raw.githubusercontent.com"
     - Etherscan: rate limiting, API key parameter injection, "result" field unwrapping

    :param url: URL to get data from
    :param model: Pydantic model to deserialize the data
    :return: deserialized response
    :raises Exception: if URL type is not supported, API key not setup, or unexpected response
    """
    with _client() as client:
        response = client.get(url, params=params).raise_for_status().content
    try:
        return TypeAdapter(model).validate_json(response)
    except ValidationError as e:
        raise Exception(f"Received unexpected response from {url}: {response.decode(errors='replace')}") from e


def _client() -> Client:
    """
    Create a new HTTP client with GitHub and Etherscan specific transports.
    :return:
    """
    cache_storage = FileStorage(base_path=xdg_cache_home() / "erc7730", ttl=7 * 24 * 3600, check_ttl_every=24 * 3600)
    http_transport = HTTPTransport()
    http_transport = GithubTransport(http_transport)
    http_transport = EtherscanTransport(http_transport)
    http_transport = CacheTransport(transport=http_transport, storage=cache_storage)
    file_transport = FileTransport()
    # TODO file storage: authorize relative paths only
    transports = {"https://": http_transport, "file://": file_transport}
    return Client(mounts=transports, timeout=10)


class DelegateTransport(ABC, BaseTransport):
    """Base class for wrapping httpx transport."""

    def __init__(self, delegate: BaseTransport) -> None:
        self._delegate = delegate

    def handle_request(self, request: Request) -> Response:
        return self._delegate.handle_request(request)

    def close(self) -> None:
        self._delegate.close()


@final
class GithubTransport(DelegateTransport):
    """GitHub specific transport for handling raw content requests."""

    GITHUB, GITHUB_RAW = "github.com", "raw.githubusercontent.com"

    def __init__(self, delegate: BaseTransport) -> None:
        super().__init__(delegate)

    @override
    def handle_request(self, request: Request) -> Response:
        if request.url.host != self.GITHUB:
            return super().handle_request(request)

        # adapt URL
        request.url = URL(str(request.url).replace(self.GITHUB, self.GITHUB_RAW).replace("/blob/", "/"))
        request.headers.update({"Host": self.GITHUB_RAW})
        return super().handle_request(request)


@final
class EtherscanTransport(DelegateTransport):
    """Etherscan specific transport for handling rate limiting, API key parameter injection, response unwrapping."""

    ETHERSCAN_API_HOST = "ETHERSCAN_API_HOST"
    ETHERSCAN_API_KEY = "ETHERSCAN_API_KEY"

    @Limiter(rate=5, capacity=5, consume=1)
    @override
    def handle_request(self, request: Request) -> Response:
        if request.url.host != ETHERSCAN:
            return super().handle_request(request)

        # substitute base URL if provided
        if (api_host := os.environ.get(self.ETHERSCAN_API_HOST)) is not None:
            request.url = request.url.copy_with(host=api_host)
            request.headers.update({"Host": api_host})

        # add API key if provided
        if (api_key := os.environ.get(self.ETHERSCAN_API_KEY)) is not None or (
            api_key := os.environ.get(f"SCAN_{self.ETHERSCAN_API_KEY}")
        ) is not None:
            request.url = request.url.copy_add_param("apikey", api_key)

        # read response
        response = super().handle_request(request)
        response.read()
        response.close()

        # unwrap result, sometimes containing JSON directly, sometimes JSON in a string
        try:
            if (result := response.json().get("result")) is not None:
                data = result if isinstance(result, str) else json.dumps(result)
                return Response(status_code=response.status_code, stream=IteratorByteStream([data.encode()]))
        except Exception:
            pass  # nosec B110 - intentional try/except/pass

        raise Exception(f"Unexpected response from Etherscan: {response.content.decode(errors='replace')}")
