import os
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


def model_from_json_file(path: Path, model: type[M]) -> M:
    """
    Load a Pydantic model from a JSON file.
    """
    with open(path) as f:
        return model.model_validate_json(f.read(), strict=True)


def model_from_json_file_or_none(path: Path, model: type[M]) -> M | None:
    """
    Load a Pydantic model from a JSON file, or None if file does not exist.
    """
    return model_from_json_file(path, model) if os.path.isfile(path) else None


def model_from_json_bytes(bytes: bytes, model: type[M]) -> M:
    """
    Load a Pydantic model from a JSON file content as an array of bytes.
    """
    return model.model_validate_json(bytes, strict=True)
