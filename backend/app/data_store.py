from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import (
    CALA_REFRESH_DEBUG_PATH,
    COMMODITIES_SEED_PATH,
    DEFAULT_GENERATED_AT,
    HISTORICAL_BENCHMARKS_SEED_PATH,
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


def load_historical_benchmarks_payload() -> dict[str, Any]:
    if not HISTORICAL_BENCHMARKS_SEED_PATH.exists():
        return {"generated_at": DEFAULT_GENERATED_AT, "series": []}
    return _load_json(HISTORICAL_BENCHMARKS_SEED_PATH)


def load_commodities_payload() -> dict[str, Any]:
    payload = _load_json(COMMODITIES_SEED_PATH)
    history_payload = load_historical_benchmarks_payload()
    history_by_commodity = {
        item["commodity"]: item
        for item in history_payload.get("series", [])
        if isinstance(item, dict) and item.get("commodity")
    }

    merged_commodities: list[dict[str, Any]] = []
    for commodity in payload["commodities"]:
        merged = dict(commodity)
        history = history_by_commodity.get(commodity["id"])
        if history:
            merged.update(
                {
                    "history_source": history.get("series_type", "local_fallback"),
                    "history_label": history.get("label", commodity["proxy_label"]),
                    "history_value_label": history.get("value_label", "Benchmark value"),
                    "history_note": history.get("source_note"),
                    "history_series": history.get("points", commodity["proxy_series"]),
                    "history_query": history.get("query"),
                }
            )
        else:
            merged.update(
                {
                    "history_source": "local_fallback",
                    "history_label": commodity["proxy_label"],
                    "history_value_label": commodity["proxy_value_label"],
                    "history_note": "Local fallback history in use until Cala benchmark seed data is generated.",
                    "history_series": commodity["proxy_series"],
                    "history_query": None,
                }
            )
        merged_commodities.append(merged)

    return {
        **payload,
        "commodities": merged_commodities,
    }


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


def write_cala_refresh_debug(payload: dict[str, Any]) -> None:
    CALA_REFRESH_DEBUG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CALA_REFRESH_DEBUG_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
