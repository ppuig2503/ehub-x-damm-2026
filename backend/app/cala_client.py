from __future__ import annotations

import hashlib
import re
import os
from datetime import datetime
from typing import Any

import httpx

from .config import DEFAULT_GENERATED_AT
from .data_store import append_refresh_log, load_seed_signals_payload, write_runtime_signals

REQUEST_TIMEOUT_SECONDS = 180.0


CALA_QUERY_MAP = {
    "aluminium": [
        {
            "driver": "energy",
            "query": "organizations.sector=aluminium.energy_costs.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Higher smelter electricity costs support aluminium procurement prices and squeeze near-term supply economics.",
        },
    ],
    "pet": [
        {
            "driver": "oil",
            "query": "organizations.sector=polyethylene terephthalate.oil.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Oil and feedstock moves pass through into PET resin cost expectations.",
        },
        {
            "driver": "regulation",
            "query": "organizations.sector=polyethylene terephthalate.regulation.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Packaging regulation and recycled-content targets shift the cost and availability of compliant PET grades.",
        },
    ],
    "energy": [
        {
            "driver": "geopolitics",
            "query": "organizations.sector=power.geopolitics.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Geopolitical shocks raise risk premia in gas and power markets relevant for industrial procurement.",
        },
    ],
    "barley": [
        {
            "driver": "weather",
            "query": "organizations.sector=agriculture.barley.weather.date>2025.limit=5.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Crop weather risk affects yield expectations and raises procurement uncertainty for barley.",
        },
    ],
}

SUMMARY_KEYS = ("summary", "Summary", "description", "Description", "text", "Text")
NAME_KEYS = ("name", "Name", "organization", "Organization", "company", "Company")
DATE_KEYS = ("date", "Date", "period", "Period")
URL_KEYS = ("source_url", "Source URL", "url", "URL")
REFERENCE_KEYS = ("sources", "Sources", "citations", "Citations", "references", "References")


def _pick_value(row: dict[str, Any], candidates: tuple[str, ...], default: str = "") -> str:
    for key in candidates:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _normalize_date(date_text: str) -> str:
    text = date_text.strip()
    if not text:
        return datetime.now().date().isoformat()

    iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if iso_match:
        return iso_match.group(1)

    month_day_year_formats = [
        "%B %d, %Y",
        "%b %d, %Y",
    ]
    for pattern in month_day_year_formats:
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue

    simple_year_match = re.search(r"\b(20\d{2})\b", text)
    if simple_year_match:
        year = int(simple_year_match.group(1))
        month_match = re.search(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
            text,
            re.IGNORECASE,
        )
        if month_match:
            try:
                return datetime.strptime(f"{month_match.group(1)} 1 {year}", "%B %d %Y").date().isoformat()
            except ValueError:
                pass
        quarter_match = re.search(r"\bQ([1-4])\b", text, re.IGNORECASE)
        if quarter_match:
            quarter = int(quarter_match.group(1))
            month = (quarter - 1) * 3 + 1
            return f"{year}-{month:02d}-01"
        return f"{year}-01-01"

    return datetime.now().date().isoformat()


def _infer_direction(driver: str, summary: str) -> str:
    lowered = summary.lower()
    bearish_terms = [
        "lower costs",
        "cost relief",
        "costs eased",
        "prices eased",
        "oversupply",
        "ample supply",
        "improved availability",
        "weaker demand",
        "soft demand",
    ]
    bullish_terms = [
        "higher costs",
        "higher",
        "rise",
        "increase",
        "tight",
        "volatility",
        "disrupt",
        "shortage",
        "support pricing",
        "pressure",
        "drought",
        "sanction",
        "deficit",
        "idled",
        "halted production",
        "elevated",
        "crisis",
        "tax",
        "mandatory",
    ]
    if any(term in lowered for term in bearish_terms):
        return "bearish"
    if any(term in lowered for term in bullish_terms):
        return "bullish"
    if driver in {"energy", "inventories", "supply", "weather", "geopolitics", "futures_prices", "PTA_MEG", "oil", "regulation"}:
        return "bullish"
    return "neutral"


def _infer_impact_score(summary: str) -> float:
    lowered = summary.lower()
    if any(term in lowered for term in ["largest cost", "support pricing", "tumbled", "lowest in over a decade", "disrupting", "volatility"]):
        return 0.84
    if any(term in lowered for term in ["increased", "wider deficit", "pressure", "tight", "higher"]):
        return 0.74
    if any(term in lowered for term in ["mixed", "steady", "offset", "adequate", "manageable"]):
        return 0.56
    return 0.66


def _infer_confidence(summary: str, date_text: str) -> float:
    score = 0.7
    if any(marker in summary.lower() for marker in ["reported", "guided", "posted", "noted", "analyst", "q1", "q2", "fy"]):
        score += 0.08
    if date_text:
        score += 0.04
    return min(0.92, round(score, 2))


def _infer_horizon(summary: str) -> str:
    lowered = summary.lower()
    if any(term in lowered for term in ["quarter", "q1", "q2", "near-term", "month"]):
        return "1-3 months"
    if any(term in lowered for term in ["year", "2026", "2027", "annual"]):
        return "3-6 months"
    return "2-6 weeks"


class CalaRefreshService:
    async def refresh(
        self,
        commodity: str | None,
        drivers: list[str] | None,
    ) -> dict[str, Any]:
        if os.getenv("SMARTBUY_FORCE_CALA_DEMO") == "1":
            payload = self._simulate_live_refresh(commodity, drivers)
            return {
                "status": "live",
                "payload": payload,
                "message": "Simulated live Cala refresh completed for demo mode.",
            }

        api_key = os.getenv("CALA_API_KEY")
        if api_key:
            try:
                payload = await self._attempt_live_refresh(api_key, commodity, drivers)
                return {
                    "status": "live",
                    "payload": payload,
                    "message": "Live Cala refresh completed.",
                    "debug_error": None,
                }
            except Exception as exc:
                payload = self._fallback_payload()
                return {
                    "status": "fallback",
                    "payload": payload,
                    "message": "Cala request failed, using the latest local snapshot.",
                    "debug_error": str(exc),
                }

        payload = self._fallback_payload()
        return {
            "status": "fallback",
            "payload": payload,
            "message": "Cala unavailable, using the latest local snapshot.",
            "debug_error": "CALA_API_KEY not found in process environment.",
        }

    async def _attempt_live_refresh(
        self,
        api_key: str,
        commodity: str | None,
        drivers: list[str] | None,
    ) -> dict[str, Any]:
        scoped_commodities = [commodity] if commodity else list(CALA_QUERY_MAP.keys())
        query_specs: list[dict[str, str]] = []
        for item in scoped_commodities:
            for spec in CALA_QUERY_MAP.get(item, []):
                if drivers and spec["driver"] not in drivers:
                    continue
                query_specs.append({"commodity": item, **spec})

        async with httpx.AsyncClient(
            base_url="https://api.cala.ai/v1",
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"X-API-KEY": api_key},
        ) as client:
            collected_signals: list[dict[str, Any]] = []
            debug_queries: list[dict[str, Any]] = []
            for spec in query_specs:
                try:
                    body = await self._run_query_with_retry(client, spec["query"])
                    results = body.get("results", []) if isinstance(body, dict) else []
                    normalized = self._normalize_results(
                        commodity=spec["commodity"],
                        driver=spec["driver"],
                        region=spec["region"],
                        mechanism=spec["mechanism"],
                        query=spec["query"],
                        results=results,
                    )
                    debug_queries.append(
                        {
                            "commodity": spec["commodity"],
                            "driver": spec["driver"],
                            "query": spec["query"],
                            "rows": len(results),
                            "signals": len(normalized),
                            "error": None,
                        }
                    )
                    collected_signals.extend(normalized)
                except Exception as exc:
                    debug_queries.append(
                        {
                            "commodity": spec["commodity"],
                            "driver": spec["driver"],
                            "query": spec["query"],
                            "rows": 0,
                            "signals": 0,
                            "error": str(exc),
                        }
                    )

        if not collected_signals:
            raise RuntimeError(f"Cala returned no usable signal rows for the configured commodity queries: {debug_queries}")

        payload = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "refresh_status": "live",
            "signals": collected_signals,
            "meta": {
                "source": "cala",
                "queries": debug_queries,
            },
        }
        payload["generated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        write_runtime_signals(payload)
        append_refresh_log(
            {
                "generated_at": payload["generated_at"],
                "status": "live",
                "commodity": commodity or "all",
                "drivers": drivers or [],
                "debug_error": None,
            }
        )
        return payload

    async def _run_query_with_retry(
        self,
        client: httpx.AsyncClient,
        query: str,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        for _ in range(2):
            try:
                response = await client.post(
                    "/knowledge/query",
                    json={"input": query, "return_entities": False},
                )
                response.raise_for_status()
                body = response.json()
                if isinstance(body, dict) and "results" in body:
                    return body
                raise RuntimeError(f"Unexpected Cala response shape: {body}")
            except (httpx.ReadTimeout, httpx.HTTPError, RuntimeError) as exc:
                last_error = exc
        raise RuntimeError(f"Cala query failed for `{query}`: {last_error}") from last_error

    def _normalize_results(
        self,
        commodity: str,
        driver: str,
        region: str,
        mechanism: str,
        query: str,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for row in results[:6]:
            if not isinstance(row, dict):
                continue
            name = _pick_value(row, NAME_KEYS, default=commodity.title())
            date_text = _pick_value(row, DATE_KEYS, default=datetime.now().date().isoformat())
            summary = _pick_value(row, SUMMARY_KEYS)
            source_url = _pick_value(row, URL_KEYS, default="https://docs.cala.ai")
            source_reference = _pick_value(row, REFERENCE_KEYS, default="")
            if not summary:
                continue
            signal_id = hashlib.md5(f"{commodity}|{driver}|{name}|{date_text}|{summary}".encode("utf-8")).hexdigest()[:16]
            if signal_id in seen_ids:
                continue
            seen_ids.add(signal_id)
            direction = _infer_direction(driver, summary)
            normalized.append(
                {
                    "id": f"cala-{commodity}-{driver}-{signal_id}",
                    "commodity": commodity,
                    "driver": driver,
                    "event": name,
                    "date": _normalize_date(date_text),
                    "region": region,
                    "direction": direction,
                    "impact_score": _infer_impact_score(summary),
                    "confidence": _infer_confidence(summary, date_text),
                    "horizon": _infer_horizon(summary),
                    "source_name": f"Cala / {name}",
                    "source_url": source_url,
                    "source_reference": source_reference or None,
                    "source_link_status": "direct" if source_url != "https://docs.cala.ai" else "fallback",
                    "evidence": summary,
                    "mechanism": mechanism,
                    "used_in_score": True,
                    "source_date": date_text,
                    "query": query,
                }
            )
        return normalized

    def _simulate_live_refresh(
        self,
        commodity: str | None,
        drivers: list[str] | None,
    ) -> dict[str, Any]:
        payload = load_seed_signals_payload()
        generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
        for signal in payload["signals"]:
            signal["date"] = generated_at[:10]
            if commodity and signal["commodity"] != commodity:
                continue
            if drivers and signal["driver"] not in drivers:
                continue
            signal["confidence"] = min(0.95, round(signal["confidence"] + 0.04, 2))
            signal["impact_score"] = min(0.95, round(signal["impact_score"] + 0.02, 2))

        payload["generated_at"] = generated_at
        payload["refresh_status"] = "live"
        payload["meta"] = {
            "source": "demo_live_refresh",
            "queries": CALA_QUERY_MAP.get(commodity, []),
        }
        write_runtime_signals(payload)
        append_refresh_log(
            {
                "generated_at": generated_at,
                "status": "live",
                "commodity": commodity or "all",
                "drivers": drivers or [],
                "debug_error": None,
            }
        )
        return payload

    def _fallback_payload(self) -> dict[str, Any]:
        payload = load_seed_signals_payload()
        payload["generated_at"] = DEFAULT_GENERATED_AT
        payload["refresh_status"] = "fallback"
        payload["meta"] = {
            "source": "local_fallback",
            "queries": [],
        }
        write_runtime_signals(payload)
        append_refresh_log(
            {
                "generated_at": DEFAULT_GENERATED_AT,
                "status": "fallback",
                "commodity": "all",
                "drivers": [],
                "debug_error": None,
            }
        )
        return payload
