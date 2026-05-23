from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .cala_client import CalaRefreshService, CalaSearchService
from .data_store import load_commodities_payload, load_scenarios_payload, load_signals_payload
from .decision_engine import SmartBuyEngine
from .models import (
    CommodityDetail,
    CalaSearchRequest,
    CalaSearchResponse,
    OverviewResponse,
    RefreshRequest,
    RefreshResponse,
    ScenarioCatalog,
    ScenarioInput,
    ScenarioResult,
)

app = FastAPI(title="SmartBuy Signal OS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_engine() -> SmartBuyEngine:
    signals_payload, refresh_status = load_signals_payload()
    commodities_payload = load_commodities_payload()
    return SmartBuyEngine(
        commodities_payload=commodities_payload,
        signals_payload=signals_payload,
        generated_at=signals_payload["generated_at"],
        refresh_status=refresh_status,
    )


@app.get("/api/v1/overview", response_model=OverviewResponse)
def get_overview() -> dict:
    return build_engine().overview_payload()


@app.get("/api/v1/commodities/{commodity_id}", response_model=CommodityDetail)
def get_commodity_detail(commodity_id: str) -> dict:
    try:
        return build_engine().detail_payload(commodity_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown commodity: {commodity_id}") from exc


@app.get("/api/v1/signals")
def get_signals(
    commodity: str | None = None,
    driver: str | None = None,
    direction: str | None = None,
    used_in_score: bool | None = None,
    min_impact: float | None = Query(default=None, ge=0, le=1),
    limit: int | None = Query(default=100, ge=1, le=500),
) -> dict:
    return build_engine().signals_payload_filtered(
        commodity=commodity,
        driver=driver,
        direction=direction,
        used_in_score=used_in_score,
        min_impact=min_impact,
        limit=limit,
    )


@app.get("/api/v1/action-plan")
def get_action_plan() -> dict:
    return build_engine().action_plan_payload()


@app.get("/api/v1/scenarios/catalog", response_model=ScenarioCatalog)
def get_scenarios_catalog() -> dict:
    return load_scenarios_payload()


@app.post("/api/v1/scenarios/evaluate", response_model=ScenarioResult)
def evaluate_scenario(payload: ScenarioInput) -> dict:
    return build_engine().scenario_payload(payload.model_dump())


@app.post("/api/v1/cala/refresh", response_model=RefreshResponse)
async def refresh_cala(payload: RefreshRequest) -> dict:
    service = CalaRefreshService()
    result = await service.refresh(payload.commodity, payload.drivers)
    refreshed_payload = result["payload"]
    return {
        "status": result["status"],
        "generated_at": refreshed_payload["generated_at"],
        "message": result["message"],
        "signals_available": len(refreshed_payload["signals"]),
        "commodity_scope": payload.commodity or "all",
        "driver_scope": payload.drivers or [],
        "debug_error": result.get("debug_error"),
    }


@app.post("/api/v1/cala/search", response_model=CalaSearchResponse)
async def search_cala(payload: CalaSearchRequest) -> dict:
    service = CalaSearchService()
    try:
        return await service.search(payload.query)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
