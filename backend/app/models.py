from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TrendPoint(BaseModel):
    date: str
    value: float
    score: float | None = None
    covid_flag: int | None = None


class Signal(BaseModel):
    id: str
    commodity: str
    driver: str
    event: str
    date: str
    region: str
    direction: Literal["bullish", "bearish", "neutral"]
    impact_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    horizon: str
    source_name: str
    source_url: str
    source_reference: str | None = None
    source_link_status: Literal["direct", "fallback"]
    evidence: str
    mechanism: str
    used_in_score: bool
    query: str | None = None


class DriverContribution(BaseModel):
    driver: str
    contribution: float
    direction: Literal["bullish", "bearish", "neutral"]
    signals: int


class DecisionRecommendation(BaseModel):
    recommended_action: Literal["buy", "wait", "hedge", "monitor"]
    suggested_coverage: str
    suggested_horizon: str
    explanation: str


class CommodityOverview(BaseModel):
    id: str
    name: str
    region: str
    risk_score: float
    confidence: float
    uncertainty_score: float
    recommended_action: Literal["buy", "wait", "hedge", "monitor"]
    suggested_coverage: str
    suggested_horizon: str
    top_driver: str
    change_note: str | None = None
    changed: bool = False
    refresh_status: Literal["seed", "fallback", "live"]
    proxy_label: str
    score_history: list[float]
    benchmark_history: list[float] | None = None
    history_source: Literal["cala_benchmark", "local_fallback"]
    history_label: str
    history_note: str | None = None
    history_start: str | None = None
    history_end: str | None = None
    history_dates: list[str] | None = None
    explanation: str


class CommodityDetail(BaseModel):
    id: str
    name: str
    region: str
    risk_score: float
    confidence: float
    uncertainty_score: float
    recommendation: DecisionRecommendation
    top_bullish_drivers: list[str]
    top_bearish_drivers: list[str]
    driver_contributions: list[DriverContribution]
    trend: list[TrendPoint]
    proxy_label: str
    proxy_value_label: str
    latest_proxy_value: float
    history_source: Literal["cala_benchmark", "local_fallback"]
    history_label: str
    history_value_label: str
    latest_history_value: float
    history_note: str | None = None
    signals: list[Signal]
    refresh_status: Literal["seed", "fallback", "live"]
    what_changed: str | None = None


class OverviewResponse(BaseModel):
    generated_at: str
    refresh_status: Literal["seed", "fallback", "live"]
    market_status: Literal["Stable", "Watch", "High Risk"]
    new_signals: dict[str, int]
    commodities: list[CommodityOverview]


class ScenarioVariableDefinition(BaseModel):
    id: str
    label: str
    type: Literal["range", "select"]
    min: float | None = None
    max: float | None = None
    step: float | None = None
    default: float | str
    options: list[str] | None = None
    applies_to: list[str]


class ScenarioCatalog(BaseModel):
    generated_at: str
    variables: list[ScenarioVariableDefinition]


class ScenarioInput(BaseModel):
    commodity: str
    energy_cost_shock: float = 0
    oil_shock: float = 0
    supply_disruption: Literal["none", "mild", "severe"] = "none"
    demand_outlook: Literal["weak", "neutral", "strong"] = "neutral"
    inventory_level: Literal["low", "normal", "high"] = "normal"
    geopolitical_risk: Literal["low", "medium", "high"] = "medium"
    weather_risk: Literal["low", "medium", "high"] = "medium"
    coverage_secured: Literal["0", "25", "50", "75"] = "0"


class ScenarioResult(BaseModel):
    commodity: str
    base_risk_score: float
    new_risk_score: float
    delta: float
    refresh_status: Literal["seed", "fallback", "live"]
    recommendation: DecisionRecommendation
    driver_impacts: list[DriverContribution]
    narrative: str


class RefreshRequest(BaseModel):
    commodity: str | None = None
    drivers: list[str] | None = None


class RefreshResponse(BaseModel):
    status: Literal["seed", "fallback", "live"]
    generated_at: str
    message: str
    signals_available: int
    commodity_scope: str
    driver_scope: list[str]
    query_count: int = 0
    duration_seconds: float | None = None
    debug_error: str | None = None


class CalaSearchRequest(BaseModel):
    query: str = Field(min_length=3)


class CalaSearchResponse(BaseModel):
    query: str
    content: str
    explainability: list[str] = Field(default_factory=list)
    context: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)


class EvidenceComparisonRequest(BaseModel):
    query: str | None = None
    commodity: str
    driver: str
    event: str
    date: str
    region: str
    evidence: str
    mechanism: str
    horizon: str


class EvidenceComparisonMatch(BaseModel):
    event: str
    date: str
    evidence: str
    source_name: str
    source_url: str
    source_reference: str | None = None


class EvidenceComparisonResponse(BaseModel):
    query: str
    count: int
    matches: list[EvidenceComparisonMatch] = Field(default_factory=list)
