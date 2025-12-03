from __future__ import annotations

import json
import pathlib
from typing import Any, Dict

import yaml


def read_yaml(path: str | pathlib.Path) -> Dict[str, Any]:
    path = pathlib.Path(path)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_json(data: Dict[str, Any] | list, path: str | pathlib.Path) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def read_json(path: str | pathlib.Path) -> Dict[str, Any] | list:
    path = pathlib.Path(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_dir(path: str | pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

