from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import (
    COMMODITIES_SEED_PATH,
    REFRESH_LOG_PATH,
    RUNTIME_SIGNALS_PATH,
    SCENARIOS_SEED_PATH,
    SIGNALS_SEED_PATH,
)


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_signals_payload() -> tuple[dict[str, Any], str]:
    if RUNTIME_SIGNALS_PATH.exists():
        payload = _load_json(RUNTIME_SIGNALS_PATH)
        status = payload.get("refresh_status", "fallback")
        return payload, status
    payload = _load_json(SIGNALS_SEED_PATH)
    return payload, payload.get("refresh_status", "seed")


def load_seed_signals_payload() -> dict[str, Any]:
    return _load_json(SIGNALS_SEED_PATH)


def load_commodities_payload() -> dict[str, Any]:
    return _load_json(COMMODITIES_SEED_PATH)


def load_scenarios_payload() -> dict[str, Any]:
    return _load_json(SCENARIOS_SEED_PATH)


def append_refresh_log(entry: dict[str, Any]) -> None:
    REFRESH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if REFRESH_LOG_PATH.exists():
        with open(REFRESH_LOG_PATH, encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        payload = {"entries": []}
    payload.setdefault("entries", []).append(entry)
    with open(REFRESH_LOG_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def write_runtime_signals(payload: dict[str, Any]) -> None:
    RUNTIME_SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNTIME_SIGNALS_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

