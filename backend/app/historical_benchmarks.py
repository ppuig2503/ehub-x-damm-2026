from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any

import httpx

from .config import DEFAULT_GENERATED_AT

HISTORY_TIMEOUT_SECONDS = 180.0
HISTORY_POINT_COUNT = 12

BENCHMARK_SPECS: dict[str, dict[str, Any]] = {
    "aluminium": {
        "label": "European aluminium benchmark",
        "value_label": "Benchmark price",
        "queries": [
            "organizations.sector=aluminium.monthly benchmark price history for Europe over the last 12 months.return(date, value, source_url)",
            "organizations.sector=aluminium.monthly benchmark price history for Europe over the last 13 months.return(date, value, source_url)",
            "organizations.sector=aluminium.price_history.date>=2025-01-01.return(date, value, source_url)",
            "aluminium.monthly price history for Europe over the last 12 months.return(date, value, source_url)",
        ],
        "source_note": "Monthly representative aluminium benchmark history sourced via Cala.",
        "fallback_note": "Local fallback history in use until a stable Cala benchmark import is available.",
        "scale_min": 2180.0,
        "scale_max": 2680.0,
    },
    "pet": {
        "label": "Europe PET resin benchmark",
        "value_label": "Benchmark price",
        "queries": [
            "Europe bottle-grade PET monthly spot price history over the last 12 months.return(date, value, source_url)",
            "organizations.sector=polyethylene terephthalate.monthly benchmark resin price history for Europe over the last 12 months.return(date, value, source_url)",
            "organizations.sector=polyethylene terephthalate.price_history.date>=2025-01-01.return(date, value, source_url)",
            "polyethylene terephthalate monthly Europe resin price history for the last 12 months.return(date, value, source_url)",
        ],
        "source_note": "Monthly representative PET resin benchmark history sourced via Cala.",
        "fallback_note": "Local fallback history in use until a stable Cala benchmark import is available.",
        "scale_min": 980.0,
        "scale_max": 1320.0,
    },
    "energy": {
        "label": "EU power benchmark",
        "value_label": "Benchmark price",
        "queries": [
            "European wholesale power monthly benchmark price history over the last 18 months.return(date, value, source_url)",
            "organizations.sector=power.monthly European power benchmark price history over the last 12 months.return(date, value, source_url)",
            "organizations.sector=power.price_history.date>=2025-01-01.return(date, value, source_url)",
            "European power monthly benchmark price history for the last 12 months.return(date, value, source_url)",
        ],
        "source_note": "Monthly representative EU power benchmark history sourced via Cala.",
        "fallback_note": "Local fallback history in use until a stable Cala benchmark import is available.",
        "scale_min": 68.0,
        "scale_max": 128.0,
    },
    "barley": {
        "label": "European feed barley benchmark",
        "value_label": "Benchmark price",
        "queries": [
            "French feed barley monthly price history over the last 12 months.return(date, value, source_url)",
            "European feed barley monthly price history over the last 12 months.return(date, value, source_url)",
            "Spain barley monthly price history over the last 12 months.return(date, value, source_url)",
            "barley price_history.date>=2025-01-01.return(date, value, source_url)",
            "malt barley monthly Europe price history for the last 12 months.return(date, value, source_url)",
        ],
        "source_note": "Monthly representative European feed barley benchmark history sourced via Cala.",
        "fallback_note": "Local fallback history in use until a stable Cala benchmark import is available.",
        "scale_min": 190.0,
        "scale_max": 255.0,
    },
}

VALUE_KEYS = ("value", "Value", "price", "Price", "benchmark_price", "benchmark")
DATE_KEYS = ("date", "Date", "month", "Month", "period", "Period")
URL_KEYS = ("source_url", "Source URL", "url", "URL")


def _pick(row: dict[str, Any], candidates: tuple[str, ...]) -> str:
    for key in candidates:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _month_start_iso(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}-01"


def _next_month(month_start: date) -> date:
    year = month_start.year + (1 if month_start.month == 12 else 0)
    month = 1 if month_start.month == 12 else month_start.month + 1
    return date(year, month, 1)


def _month_sequence(end_month: str, count: int = HISTORY_POINT_COUNT) -> list[str]:
    end = datetime.strptime(end_month, "%Y-%m-%d").date().replace(day=1)
    months: list[str] = []
    year = end.year
    month = end.month
    for _ in range(count):
        months.append(_month_start_iso(year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()
    return months


def _expand_months(text: str) -> list[str]:
    value = text.strip()
    if not value:
        return []
    range_match = re.match(r"^(\d{4}-\d{2})\s+to\s+(\d{4}-\d{2})$", value)
    if range_match:
        start = datetime.strptime(f"{range_match.group(1)}-01", "%Y-%m-%d").date()
        end = datetime.strptime(f"{range_match.group(2)}-01", "%Y-%m-%d").date()
        months: list[str] = []
        current = start
        while current <= end:
            months.append(current.isoformat())
            current = _next_month(current)
        return months
    quarter_match = re.match(r"^(\d{4})-Q([1-4])$", value)
    if quarter_match:
        year = int(quarter_match.group(1))
        quarter = int(quarter_match.group(2))
        start_month = (quarter - 1) * 3 + 1
        return [
            _month_start_iso(year, start_month),
            _month_start_iso(year, start_month + 1),
            _month_start_iso(year, start_month + 2),
        ]
    patterns = [
        "%Y-%m-%d",
        "%Y-%m",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %Y",
        "%b %Y",
    ]
    for pattern in patterns:
        try:
            parsed = datetime.strptime(value, pattern)
            return [parsed.date().replace(day=1).isoformat()]
        except ValueError:
            continue
    if len(value) == 4 and value.isdigit():
        return [f"{value}-01-01"]
    return []


def _parse_float(value: str) -> float | None:
    multiplier = 1.0
    if "/kg" in value.lower():
        multiplier = 1000.0

    normalized = (
        value.replace("≈", "~")
        .replace("–", "-")
        .replace("—", "-")
        .replace("*", "")
        .replace("~", "")
        .replace(">", "")
        .replace("<", "")
    )
    if "-" in normalized:
        parts = [part.strip() for part in normalized.split("-") if part.strip()]
        values = []
        for item in parts[:2]:
            matches = re.findall(r"\d+(?:\.\d+)?", item.replace(",", ""))
            if matches:
                values.append(float(matches[0]))
        if len(values) == 2:
            return round(sum(values) / 2, 2)
    cleaned = (
        normalized.replace(",", "")
        .replace("€", "")
        .replace("C$", "")
        .replace("$", "")
        .replace("EUR", "")
        .replace("USD", "")
        .replace("CAD", "")
        .replace("/tonne", "")
        .replace("/t", "")
        .replace("/MWh", "")
        .replace("/kg", "")
        .replace("/metric ton", "")
        .replace("metric ton", "")
        .replace("¢/lb", "")
        .strip()
    )
    matches = re.findall(r"\d+(?:\.\d+)?", cleaned)
    if not matches:
        return None
    return float(matches[0]) * multiplier


def _build_dense_month_points(
    by_month: dict[str, list[float]],
    source_urls: dict[str, str | None],
    end_month: str,
) -> list[dict[str, Any]]:
    target_months = _month_sequence(end_month)
    available = {
        month: round(sum(values) / len(values), 2)
        for month, values in by_month.items()
        if month in target_months
    }
    if len(available) < 6:
        return []

    known_indices = [index for index, month in enumerate(target_months) if month in available]
    points: list[dict[str, Any]] = []
    for index, month in enumerate(target_months):
        if month in available:
            points.append(
                {
                    "date": month,
                    "value": available[month],
                    "source_url": source_urls.get(month),
                }
            )
            continue

        previous_indices = [known for known in known_indices if known < index]
        next_indices = [known for known in known_indices if known > index]
        if previous_indices and next_indices:
            lower = previous_indices[-1]
            upper = next_indices[0]
            lower_value = available[target_months[lower]]
            upper_value = available[target_months[upper]]
            ratio = (index - lower) / (upper - lower)
            value = lower_value + (upper_value - lower_value) * ratio
            source_url = source_urls.get(target_months[lower]) or source_urls.get(target_months[upper])
        elif previous_indices:
            lower = previous_indices[-1]
            value = available[target_months[lower]]
            source_url = source_urls.get(target_months[lower])
        elif next_indices:
            upper = next_indices[0]
            value = available[target_months[upper]]
            source_url = source_urls.get(target_months[upper])
        else:
            return []

        points.append(
            {
                "date": month,
                "value": round(value, 2),
                "source_url": source_url,
            }
        )

    return points


def normalize_cala_history_rows(rows: list[dict[str, Any]], end_month: str | None = None) -> list[dict[str, Any]]:
    by_month: dict[str, list[float]] = {}
    source_urls: dict[str, str | None] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        months = _expand_months(_pick(row, DATE_KEYS))
        value = _parse_float(_pick(row, VALUE_KEYS))
        if not months or value is None:
            continue
        for month in months:
            by_month.setdefault(month, []).append(value)
            source_urls.setdefault(month, _pick(row, URL_KEYS) or None)

    months = sorted(by_month.keys())
    if len(months) < HISTORY_POINT_COUNT - 1:
        if end_month:
            return _build_dense_month_points(by_month, source_urls, end_month)
        return []
    selected = months[-HISTORY_POINT_COUNT:]
    points = [
        {
            "date": item,
            "value": round(sum(by_month[item]) / len(by_month[item]), 2),
            "source_url": source_urls.get(item),
        }
        for item in selected
    ]
    if len(points) == HISTORY_POINT_COUNT - 1:
        last = points[-1]
        points.append(
            {
                "date": _next_month(datetime.strptime(last["date"], "%Y-%m-%d").date()).isoformat(),
                "value": last["value"],
                "source_url": last.get("source_url"),
            }
        )
    return points if len(points) == HISTORY_POINT_COUNT else []


def _interpolate(values: list[float], position: float) -> float:
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    if lower == upper:
        return values[lower]
    ratio = position - lower
    return values[lower] + (values[upper] - values[lower]) * ratio


def build_local_fallback_points(
    commodity_payload: dict[str, Any],
    scale_min: float,
    scale_max: float,
    end_month: str,
) -> list[dict[str, Any]]:
    source_values = [float(point["value"]) for point in commodity_payload["proxy_series"]]
    local_min = min(source_values)
    local_max = max(source_values)
    local_range = (local_max - local_min) or 1.0
    dates = _month_sequence(end_month)
    points: list[dict[str, Any]] = []
    for index, month in enumerate(dates):
        position = (index / (HISTORY_POINT_COUNT - 1)) * (len(source_values) - 1)
        sampled = _interpolate(source_values, position)
        normalized = (sampled - local_min) / local_range
        value = scale_min + normalized * (scale_max - scale_min)
        points.append({"date": month, "value": round(value, 2)})
    return points


def build_fallback_entry(commodity_payload: dict[str, Any], end_month: str) -> dict[str, Any]:
    commodity_id = commodity_payload["id"]
    spec = BENCHMARK_SPECS[commodity_id]
    return {
        "commodity": commodity_id,
        "series_type": "local_fallback",
        "label": spec["label"],
        "value_label": spec["value_label"],
        "source_note": spec["fallback_note"],
        "query": spec["queries"][0],
        "diagnostics": [],
        "points": build_local_fallback_points(
            commodity_payload=commodity_payload,
            scale_min=spec["scale_min"],
            scale_max=spec["scale_max"],
            end_month=end_month,
        ),
    }


def build_seed_history_payload(commodities_payload: dict[str, Any], end_month: str) -> dict[str, Any]:
    entries = [
        build_fallback_entry(commodity, end_month)
        for commodity in commodities_payload["commodities"]
        if commodity["id"] in BENCHMARK_SPECS
    ]
    return {
        "generated_at": DEFAULT_GENERATED_AT,
        "source": "seed_offline",
        "series": entries,
    }


def fetch_history_entry(
    client: httpx.Client,
    commodity_payload: dict[str, Any],
    end_month: str,
) -> dict[str, Any]:
    commodity_id = commodity_payload["id"]
    spec = BENCHMARK_SPECS[commodity_id]
    diagnostics: list[dict[str, Any]] = []
    for query in spec["queries"]:
        try:
            response = client.post(
                "/knowledge/query",
                json={"input": query, "return_entities": False},
            )
            response.raise_for_status()
            body = response.json()
            rows = body.get("results", []) if isinstance(body, dict) else []
            points = normalize_cala_history_rows(rows, end_month=end_month)
            diagnostics.append(
                {
                    "query": query,
                    "status": "ok",
                    "rows": len(rows),
                    "normalized_points": len(points),
                }
            )
            if len(points) == HISTORY_POINT_COUNT:
                return {
                    "commodity": commodity_id,
                    "series_type": "cala_benchmark",
                    "label": spec["label"],
                    "value_label": spec["value_label"],
                    "source_note": spec["source_note"],
                    "query": query,
                    "diagnostics": diagnostics,
                    "points": points,
                }
        except Exception as exc:
            diagnostics.append(
                {
                    "query": query,
                    "status": "error",
                    "rows": 0,
                    "normalized_points": 0,
                    "error": str(exc),
                }
            )
    fallback = build_fallback_entry(commodity_payload, end_month)
    fallback["diagnostics"] = diagnostics
    return fallback


def build_historical_benchmarks_payload(
    commodities_payload: dict[str, Any],
    api_key: str | None = None,
    live: bool = False,
    end_month: str | None = None,
) -> dict[str, Any]:
    resolved_end_month = end_month or datetime.fromisoformat(
        DEFAULT_GENERATED_AT.replace("Z", "+00:00")
    ).date().replace(day=1).isoformat()

    if not live or not api_key:
        return build_seed_history_payload(commodities_payload, resolved_end_month)

    entries: list[dict[str, Any]] = []
    with httpx.Client(
        base_url="https://api.cala.ai/v1",
        timeout=HISTORY_TIMEOUT_SECONDS,
        headers={"X-API-KEY": api_key},
    ) as client:
        for commodity in commodities_payload["commodities"]:
            if commodity["id"] not in BENCHMARK_SPECS:
                continue
            entries.append(fetch_history_entry(client, commodity, resolved_end_month))

    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": "cala_live_attempt",
        "series": entries,
    }
