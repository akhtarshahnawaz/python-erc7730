from typing import Type

import requests
from pydantic import RootModel

from erc7730.model.abi import ABI

ETHERSCAN_API_KEY = "PACYAZQRENDI4TUKRTA8YAQZ4R8KVETHAE"


def get_contract_abis(contract_address: str) -> list[ABI]:
    resp = requests.get(
        f"https://api.etherscan.io/api"
        f"?module=contract"
        f"&action=getabi"
        f"&address={contract_address}"
        f"&apikey={ETHERSCAN_API_KEY}"
    )
    resp.raise_for_status()
    model: Type[RootModel[list[ABI]]] = RootModel[list[ABI]]
    json = resp.json()
    return model.model_validate_json(json["result"]).root
