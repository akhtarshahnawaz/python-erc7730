from typing import Type

import requests
from pydantic import RootModel
import os
from erc7730.model.abi import ABI


def get_contract_abis(contract_address: str) -> list[ABI] | None:
    if (api_key := os.environ.get("ETHERSCAN_API_KEY")) is None:
        return None
    resp = requests.get(
        f"https://api.etherscan.io/api"
        f"?module=contract"
        f"&action=getabi"
        f"&address={contract_address}"
        f"&apikey={api_key}"
    )
    resp.raise_for_status()
    model: Type[RootModel[list[ABI]]] = RootModel[list[ABI]]
    json = resp.json()
    return model.model_validate_json(json["result"]).root
