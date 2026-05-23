from __future__ import annotations

import hashlib
import re
import os
from datetime import datetime
from typing import Any

import httpx

from .config import DEFAULT_GENERATED_AT
from .data_store import append_refresh_log, load_seed_signals_payload, write_runtime_signals

REQUEST_TIMEOUT_SECONDS = 600.0


CALA_QUERY_MAP = {
    "aluminium": [
        {
            "driver": "energy",
            "query": "organizations.sector=aluminium.energy_costs.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Higher smelter electricity costs support aluminium procurement prices and squeeze near-term supply economics.",
        },
        {
            "driver": "inventories",
            "query": "organizations.sector=aluminium.inventories.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Inventory drawdowns tighten prompt availability while stock builds ease near-term procurement pressure.",
        },
        {
            "driver": "demand",
            "query": "organizations.sector=aluminium.demand.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "End-market demand in autos, construction, and packaging shifts aluminium procurement urgency.",
        },
        {
            "driver": "imports_exports",
            "query": "organizations.sector=aluminium.imports_exports.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Trade flows, import availability, and export controls alter regional aluminium supply pressure.",
        },
        {
            "driver": "supply",
            "query": "organizations.sector=aluminium.supply_disruptions.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Operational outages or supply disruptions reduce primary metal availability and lift procurement risk.",
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
        {
            "driver": "PTA_MEG",
            "query": "organizations.sector=polyethylene terephthalate.pta_meg.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "PTA and MEG feedstock moves affect PET resin conversion costs and price expectations.",
        },
        {
            "driver": "supply",
            "query": "organizations.sector=polyethylene terephthalate.supply.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Plant operating rates and resin availability change prompt PET procurement conditions.",
        },
        {
            "driver": "imports_exports",
            "query": "organizations.sector=polyethylene terephthalate.imports_exports.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Imported resin offers and trade restrictions shift the cost of securing PET volumes.",
        },
        {
            "driver": "demand",
            "query": "organizations.sector=polyethylene terephthalate.demand.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Beverage and packaging demand moves influence PET tightness and buying urgency.",
        },
    ],
    "energy": [
        {
            "driver": "geopolitics",
            "query": "organizations.sector=power.geopolitics.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Geopolitical shocks raise risk premia in gas and power markets relevant for industrial procurement.",
        },
        {
            "driver": "weather",
            "query": "organizations.sector=power.weather.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Weather-driven swings in renewables, hydro, heating, and cooling demand alter power market tightness.",
        },
        {
            "driver": "inventories",
            "query": "organizations.sector=power.inventories.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Gas storage and fuel inventories shape short-term resilience and procurement risk in power markets.",
        },
        {
            "driver": "demand",
            "query": "organizations.sector=power.demand.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Industrial and seasonal demand swings change the urgency of power procurement decisions.",
        },
        {
            "driver": "supply",
            "query": "organizations.sector=power.supply.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Generation outages and supply constraints tighten power availability and raise procurement pressure.",
        },
        {
            "driver": "futures_prices",
            "query": "organizations.sector=power.futures_prices.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Forward power and fuel prices signal how much procurement risk the market is pricing in.",
        },
    ],
    "barley": [
        {
            "driver": "weather",
            "query": "organizations.sector=agriculture.barley.weather.date>2025.limit=5.return(name, date, summary, source_url, sources)",
            "region": "Europe",
            "mechanism": "Crop weather risk affects yield expectations and raises procurement uncertainty for barley.",
        },
        {
            "driver": "imports_exports",
            "query": "organizations.sector=agriculture.barley.imports_exports.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Trade flows and import dependence influence barley availability and replacement costs.",
        },
        {
            "driver": "supply",
            "query": "organizations.sector=agriculture.barley.supply.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Production shortfalls or abundant harvests directly affect barley procurement pressure.",
        },
        {
            "driver": "demand",
            "query": "organizations.sector=agriculture.barley.demand.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Brewing, feed, and export demand shifts affect how tight the barley balance feels for buyers.",
        },
        {
            "driver": "inventories",
            "query": "organizations.sector=agriculture.barley.stocks.date>2025.return(name, date, summary, source_url, sources)",
            "region": "Global",
            "mechanism": "Stocks and carryover levels buffer or amplify barley procurement risk.",
        },
    ],
}

SUMMARY_KEYS = ("summary", "Summary", "description", "Description", "text", "Text")
NAME_KEYS = ("name", "Name", "organization", "Organization", "company", "Company")
DATE_KEYS = ("date", "Date", "period", "Period")
URL_KEYS = ("source_url", "Source URL", "url", "URL")
REFERENCE_KEYS = ("sources", "Sources", "citations", "Citations", "references", "References")
DIRECT_RISK_UP_TERMS = [
    "higher costs",
    "cost inflation",
    "price increase",
    "prices rose",
    "prices rise",
    "tight supply",
    "tightness",
    "shortage",
    "volatility",
    "disrupt",
    "deficit",
    "idled",
    "halted production",
    "outage",
    "sanction",
    "drought",
    "heat stress",
    "low stocks",
    "drawdown",
    "storage below",
]
DIRECT_RISK_DOWN_TERMS = [
    "lower costs",
    "cost relief",
    "prices eased",
    "prices fell",
    "price decline",
    "oversupply",
    "ample supply",
    "stock build",
    "inventory build",
    "improved availability",
    "better availability",
    "soft demand",
    "weaker demand",
    "surplus",
    "record harvest",
]
DRIVER_DIRECTION_RULES = {
    "energy": {
        "bullish": ["higher power", "electricity costs", "energy costs", "gas prices", "tariff", "expensive electricity"],
        "bearish": ["lower power", "cheaper electricity", "energy relief", "power costs eased"],
    },
    "inventories": {
        "bullish": ["drawdown", "low inventory", "low stocks", "tight stocks", "storage below"],
        "bearish": ["stock build", "inventory build", "ample stocks", "high inventory", "high stocks"],
    },
    "demand": {
        "bullish": ["strong demand", "demand growth", "robust demand", "recovery in demand"],
        "bearish": ["weak demand", "soft demand", "demand slowdown", "lower demand"],
    },
    "imports_exports": {
        "bullish": ["export restriction", "export ban", "import dependence", "trade disruption", "tariff increase"],
        "bearish": ["higher imports", "import availability", "more imports", "trade flows improved"],
    },
    "supply": {
        "bullish": ["outage", "shutdown", "disruption", "maintenance", "reduced output", "lower production"],
        "bearish": ["restart", "capacity increase", "production recovery", "higher output", "supply improved"],
    },
    "oil": {
        "bullish": ["higher crude", "oil volatility", "feedstock costs", "sanction", "supply risk"],
        "bearish": ["lower crude", "oil prices eased", "feedstock relief", "refining margin pressure down"],
    },
    "PTA_MEG": {
        "bullish": ["pta rose", "meg rose", "feedstock increase", "spread widened", "cost push"],
        "bearish": ["pta fell", "meg fell", "spread narrowed", "feedstock eased"],
    },
    "regulation": {
        "bullish": ["tax", "mandatory", "compliance cost", "recycled content target", "producer responsibility fee"],
        "bearish": ["relief", "delay", "exemption", "support subsidy", "lower compliance burden"],
    },
    "geopolitics": {
        "bullish": ["crisis", "conflict", "sanction", "blockade", "war risk", "closure"],
        "bearish": ["ceasefire", "stabilized", "risk eased", "flows restored", "de-escalation"],
    },
    "weather": {
        "bullish": ["drought", "heat stress", "frost", "flooding", "yield risk", "crop stress"],
        "bearish": ["favorable weather", "good rainfall", "yield improvement", "benign conditions"],
    },
    "futures_prices": {
        "bullish": ["futures rose", "forward curve higher", "backwardation", "premium widened"],
        "bearish": ["futures fell", "forward curve eased", "contango", "premium narrowed"],
    },
}


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


def _normalize_text_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        normalized: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                normalized.append(item.strip())
            elif isinstance(item, dict):
                text_value = (
                    item.get("content")
                    or item.get("summary")
                    or item.get("text")
                    or item.get("name")
                )
                if text_value:
                    normalized.append(str(text_value).strip())
        return normalized
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _normalize_entity_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        normalized: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                normalized.append(item.strip())
            elif isinstance(item, dict):
                name = item.get("name") or item.get("title") or item.get("id")
                if name:
                    normalized.append(str(name).strip())
        return normalized
    return []


def _infer_direction(driver: str, summary: str) -> str:
    lowered = summary.lower()
    rules = DRIVER_DIRECTION_RULES.get(driver, {})
    bullish_terms = rules.get("bullish", [])
    bearish_terms = rules.get("bearish", [])
    if any(term in lowered for term in bearish_terms):
        return "bearish"
    if any(term in lowered for term in bullish_terms):
        return "bullish"
    if any(term in lowered for term in DIRECT_RISK_DOWN_TERMS):
        return "bearish"
    if any(term in lowered for term in DIRECT_RISK_UP_TERMS):
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


class CalaSearchService:
    async def search(self, query: str) -> dict[str, Any]:
        api_key = os.getenv("CALA_API_KEY")
        if not api_key:
            raise RuntimeError("CALA_API_KEY not found in process environment.")

        async with httpx.AsyncClient(
            base_url="https://api.cala.ai/v1",
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"X-API-KEY": api_key},
        ) as client:
            response = await client.post(
                "/knowledge/search",
                json={"input": query},
            )
            response.raise_for_status()
            body = response.json()

        if not isinstance(body, dict):
            raise RuntimeError(f"Unexpected Cala search response shape: {body}")

        return {
            "query": query,
            "content": str(body.get("content", "")).strip() or "Cala returned an empty answer.",
            "explainability": _normalize_text_list(body.get("explainability")),
            "context": _normalize_text_list(body.get("context")),
            "entities": _normalize_entity_list(body.get("entities")),
        }
