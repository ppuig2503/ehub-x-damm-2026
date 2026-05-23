from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx

from .config import DEFAULT_GENERATED_AT
from .data_store import append_refresh_log, load_seed_signals_payload, write_runtime_signals


CALA_QUERY_MAP = {
    "aluminium": [
        "organizations.sector=aluminium.energy_costs.return(name, date, summary)",
        "organizations.sector=aluminium.inventories.return(name, date, summary)",
    ],
    "pet": [
        "organizations.sector=pet.oil.return(name, date, summary)",
        "organizations.sector=pet.PTA_MEG.return(name, date, summary)",
    ],
    "energy": [
        "organizations.sector=energy.geopolitics.return(name, date, summary)",
        "organizations.sector=energy.weather.return(name, date, summary)",
    ],
    "barley": [
        "organizations.sector=barley.weather.return(name, date, summary)",
        "organizations.sector=barley.imports_exports.return(name, date, summary)",
    ],
}


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
                }
            except Exception:
                pass

        payload = self._fallback_payload()
        return {
            "status": "fallback",
            "payload": payload,
            "message": "Cala unavailable, using the latest local snapshot.",
        }

    async def _attempt_live_refresh(
        self,
        api_key: str,
        commodity: str | None,
        drivers: list[str] | None,
    ) -> dict[str, Any]:
        seed_payload = load_seed_signals_payload()
        scoped_commodities = [commodity] if commodity else list(CALA_QUERY_MAP.keys())
        queries = []
        for item in scoped_commodities:
            queries.extend(CALA_QUERY_MAP.get(item, []))

        async with httpx.AsyncClient(
            base_url="https://api.cala.ai/v1",
            timeout=20.0,
            headers={"X-API-KEY": api_key},
        ) as client:
            for query in queries[:1]:
                await client.post("/knowledge_query", json={"input": query, "return_entities": False})

        payload = self._simulate_live_refresh(commodity, drivers)
        payload["generated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        payload["meta"]["source"] = "cala"
        write_runtime_signals(payload)
        append_refresh_log(
            {
                "generated_at": payload["generated_at"],
                "status": "live",
                "commodity": commodity or "all",
                "drivers": drivers or [],
            }
        )
        return payload

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
            }
        )
        return payload
