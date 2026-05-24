from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from statistics import mean, pstdev
from typing import Any

from .config import COMMODITY_DRIVER_MAP, COMMODITY_NAMES, DRIVER_WEIGHT_LEVELS


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def parse_date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def direction_sign(direction: str) -> int:
    if direction == "bullish":
        return 1
    if direction == "bearish":
        return -1
    return 0


@dataclass
class CommodityComputation:
    overview: dict[str, Any]
    detail: dict[str, Any]


class DammBuyEngine:
    def __init__(
        self,
        commodities_payload: dict[str, Any],
        signals_payload: dict[str, Any],
        generated_at: str,
        refresh_status: str,
    ) -> None:
        self.commodities_payload = commodities_payload
        self.signals_payload = signals_payload
        self.generated_at = generated_at
        self.refresh_status = refresh_status

    def _signals_for(self, commodity_id: str) -> list[dict[str, Any]]:
        return [
            signal
            for signal in self.signals_payload["signals"]
            if signal["commodity"] == commodity_id
        ]

    def _compute_trend(
        self,
        commodity: dict[str, Any],
        current_risk_score: float,
        external_score: float,
    ) -> list[dict[str, Any]]:
        chart_series = commodity.get("history_series", commodity["proxy_series"])
        values = [point["value"] for point in chart_series]
        base_mean = mean(values)
        base_std = pstdev(values) if len(values) > 1 else 1
        trend: list[dict[str, Any]] = []
        for point in chart_series:
            proxy_normalized = 50 + ((point["value"] - base_mean) / base_std) * 10
            score = clamp((proxy_normalized * 0.35) + (external_score * 0.65), 0, 100)
            trend.append(
                {
                    "date": point["date"],
                    "value": round(point["value"], 2),
                    "score": round(score, 1),
                    "covid_flag": point.get("covid_flag"),
                }
            )
        if trend:
            trend[-1]["score"] = round(current_risk_score, 1)
        return trend

    def _recommendation(
        self,
        risk_score: float,
        uncertainty_score: float,
        bullish_drivers: list[str],
        bearish_drivers: list[str],
    ) -> dict[str, str]:
        if risk_score >= 75 and uncertainty_score >= 55:
            action = "hedge"
            coverage = "40-60%"
            horizon = "1-3 months"
        elif risk_score >= 68 and uncertainty_score < 50:
            action = "buy"
            coverage = "60-80%"
            horizon = "1 month"
        elif risk_score >= 55:
            action = "hedge"
            coverage = "20-40%"
            horizon = "2-4 weeks"
        elif risk_score >= 40:
            action = "monitor"
            coverage = "0-20%"
            horizon = "2 weeks"
        else:
            action = "wait"
            coverage = "0%"
            horizon = "review in 2-4 weeks"

        bullish_text = ", ".join(bullish_drivers[:2]) if bullish_drivers else "mixed signals"
        bearish_text = ", ".join(bearish_drivers[:2]) if bearish_drivers else "limited bearish pressure"
        explanation = (
            f"Recommendation leans {action} because bullish pressure is led by {bullish_text}, "
            f"while bearish pressure is driven by {bearish_text}. "
            f"Uncertainty is {uncertainty_score:.0f}/100, so coverage is kept at {coverage}."
        )
        return {
            "recommended_action": action,
            "suggested_coverage": coverage,
            "suggested_horizon": horizon,
            "explanation": explanation,
        }

    def _compute_one(
        self,
        commodity: dict[str, Any],
        scenario_delta: dict[str, float] | None = None,
    ) -> CommodityComputation:
        commodity_id = commodity["id"]
        signals = self._signals_for(commodity_id)
        driver_totals: dict[str, float] = defaultdict(float)
        driver_signal_counts: dict[str, int] = defaultdict(int)
        bullish_confidences: list[float] = []
        bearish_confidences: list[float] = []
        used_signals: list[dict[str, Any]] = []

        for signal in signals:
            if not signal["used_in_score"]:
                continue
            weight_level = COMMODITY_DRIVER_MAP[commodity_id].get(signal["driver"], "low")
            driver_weight = DRIVER_WEIGHT_LEVELS[weight_level]
            contribution = (
                direction_sign(signal["direction"])
                * signal["impact_score"]
                * signal["confidence"]
                * driver_weight
                * 18
            )
            driver_totals[signal["driver"]] += contribution
            driver_signal_counts[signal["driver"]] += 1
            used_signals.append(signal)
            if signal["direction"] == "bullish":
                bullish_confidences.append(signal["confidence"])
            elif signal["direction"] == "bearish":
                bearish_confidences.append(signal["confidence"])

        for driver, delta in (scenario_delta or {}).items():
            driver_totals[driver] += delta

        driver_contributions: list[dict[str, Any]] = []
        for driver, contribution in driver_totals.items():
            direction = "neutral"
            if contribution > 0:
                direction = "bullish"
            elif contribution < 0:
                direction = "bearish"
            driver_contributions.append(
                {
                    "driver": driver,
                    "contribution": round(contribution, 1),
                    "direction": direction,
                    "signals": driver_signal_counts.get(driver, 0),
                }
            )
        driver_contributions.sort(key=lambda item: abs(item["contribution"]), reverse=True)

        external_signal_score = clamp(50 + sum(driver_totals.values()), 0, 100)
        proxy_score = float(commodity["proxy_score"])
        volatility_component = float(commodity.get("volatility_index", 12)) / 25
        risk_score = clamp(
            (external_signal_score * 0.7) + (proxy_score * 0.3),
            0,
            100,
        )

        bullish_count = len(bullish_confidences)
        bearish_count = len(bearish_confidences)
        used_count = len(used_signals) or 1
        conflicting_ratio = min(bullish_count, bearish_count) / used_count
        avg_confidence = mean(
            [signal["confidence"] for signal in used_signals]
        ) if used_signals else 0.5
        low_confidence_penalty = max(0.0, 0.75 - avg_confidence) / 0.75
        sparse_penalty = 0.25 if used_count >= 4 else 0.65
        uncertainty_score = clamp(
            100
            * (
                conflicting_ratio * 0.4
                + low_confidence_penalty * 0.25
                + volatility_component * 0.2
                + sparse_penalty * 0.15
            ),
            12,
            88,
        )
        confidence = clamp(
            avg_confidence * 100
            - conflicting_ratio * 18
            - volatility_component * 9
            + min(used_count, 6) * 3.2,
            36,
            91,
        )

        bullish_drivers = [
            item["driver"].replace("_", " ")
            for item in driver_contributions
            if item["contribution"] > 0
        ]
        bearish_drivers = [
            item["driver"].replace("_", " ")
            for item in driver_contributions
            if item["contribution"] < 0
        ]

        recommendation = self._recommendation(
            risk_score,
            uncertainty_score,
            bullish_drivers,
            bearish_drivers,
        )

        previous = commodity.get("previous_snapshot", {})
        changed = (
            previous.get("recommended_action") != recommendation["recommended_action"]
            or abs(previous.get("risk_score", risk_score) - risk_score) >= 6
        )
        if changed:
            change_note = (
                f"Moved from {previous.get('recommended_action', 'monitor')} "
                f"({previous.get('risk_score', risk_score):.0f}) to "
                f"{recommendation['recommended_action']} ({risk_score:.0f})."
            )
        else:
            change_note = "Recommendation stable versus the previous snapshot."

        explanation = recommendation["explanation"]
        trend = self._compute_trend(
            commodity,
            current_risk_score=risk_score,
            external_score=external_signal_score,
        )

        history_slice = trend[-12:] if trend else []
        history_start = history_slice[0]["date"] if history_slice else None
        history_end = history_slice[-1]["date"] if history_slice else None
        history_dates = [point["date"] for point in history_slice]

        overview = {
            "id": commodity_id,
            "name": COMMODITY_NAMES[commodity_id],
            "region": commodity["region"],
            "risk_score": round(risk_score, 1),
            "confidence": round(confidence, 1),
            "uncertainty_score": round(uncertainty_score, 1),
            "recommended_action": recommendation["recommended_action"],
            "suggested_coverage": recommendation["suggested_coverage"],
            "suggested_horizon": recommendation["suggested_horizon"],
            "top_driver": (
                driver_contributions[0]["driver"].replace("_", " ")
                if driver_contributions
                else "mixed"
            ),
            "change_note": change_note,
            "changed": changed,
            "refresh_status": self.refresh_status,
            "proxy_label": commodity["proxy_label"],
            "score_history": [point["score"] for point in trend[-12:]],
            "benchmark_history": (
                [point["value"] for point in trend[-12:]]
                if trend
                else None
            ),
            "history_source": commodity.get("history_source", "local_fallback"),
            "history_label": commodity.get("history_label", commodity["proxy_label"]),
            "history_note": commodity.get("history_note"),
            "history_start": history_start,
            "history_end": history_end,
            "history_dates": history_dates,
            "explanation": explanation,
        }

        detail = {
            "id": commodity_id,
            "name": COMMODITY_NAMES[commodity_id],
            "region": commodity["region"],
            "risk_score": round(risk_score, 1),
            "confidence": round(confidence, 1),
            "uncertainty_score": round(uncertainty_score, 1),
            "recommendation": recommendation,
            "top_bullish_drivers": bullish_drivers[:3],
            "top_bearish_drivers": bearish_drivers[:3],
            "driver_contributions": driver_contributions,
            "trend": trend,
            "proxy_label": commodity["proxy_label"],
            "proxy_value_label": commodity["proxy_value_label"],
            "latest_proxy_value": round(trend[-1]["value"], 2),
            "history_source": commodity.get("history_source", "local_fallback"),
            "history_label": commodity.get("history_label", commodity["proxy_label"]),
            "history_value_label": commodity.get("history_value_label", commodity["proxy_value_label"]),
            "latest_history_value": round(trend[-1]["value"], 2),
            "history_note": commodity.get("history_note"),
            "signals": signals,
            "refresh_status": self.refresh_status,
            "what_changed": change_note,
        }
        return CommodityComputation(overview=overview, detail=detail)

    def compute_all(self) -> dict[str, CommodityComputation]:
        return {
            commodity["id"]: self._compute_one(commodity)
            for commodity in self.commodities_payload["commodities"]
        }

    def overview_payload(self) -> dict[str, Any]:
        computed = self.compute_all()
        commodities = [item.overview for item in computed.values()]
        commodities.sort(key=lambda item: item["risk_score"], reverse=True)
        max_risk = max(item["risk_score"] for item in commodities)
        market_status = "Stable"
        if max_risk >= 75:
            market_status = "High Risk"
        elif max_risk >= 55:
            market_status = "Watch"

        generated_at_date = parse_date(self.generated_at)
        signal_dates = [parse_date(signal["date"]) for signal in self.signals_payload["signals"]]
        new_signals = {
            "24h": sum((generated_at_date - signal_date).days <= 1 for signal_date in signal_dates),
            "48h": sum((generated_at_date - signal_date).days <= 2 for signal_date in signal_dates),
            "72h": sum((generated_at_date - signal_date).days <= 3 for signal_date in signal_dates),
        }
        return {
            "generated_at": self.generated_at,
            "refresh_status": self.refresh_status,
            "market_status": market_status,
            "new_signals": new_signals,
            "commodities": commodities,
        }

    def detail_payload(self, commodity_id: str) -> dict[str, Any]:
        computed = self.compute_all()
        if commodity_id not in computed:
            raise KeyError(commodity_id)
        return computed[commodity_id].detail

    def action_plan_payload(self) -> dict[str, Any]:
        overview = self.overview_payload()
        ranked = sorted(overview["commodities"], key=lambda item: item["risk_score"], reverse=True)
        memo = (
            f"This week DammBuy prioritises {ranked[0]['name']} and {ranked[1]['name']} for action. "
            f"{ranked[0]['name']} sits at {ranked[0]['risk_score']:.0f}/100 with a "
            f"{ranked[0]['recommended_action']} recommendation, while {ranked[-1]['name']} remains "
            f"lower urgency and better suited to {ranked[-1]['recommended_action']}."
        )
        triggers = [
            "Energy cost shock above 10%",
            "Inventory drawdown beyond 15%",
            "New trade restriction or tariff signal",
            "Proxy volatility breaks recent range",
            "Barley benchmark moves materially versus the recent monthly range",
        ]
        return {
            "generated_at": self.generated_at,
            "refresh_status": self.refresh_status,
            "priorities": ranked,
            "memo": memo,
            "triggers": triggers,
        }

    def signals_payload_filtered(
        self,
        commodity: str | None = None,
        driver: str | None = None,
        direction: str | None = None,
        used_in_score: bool | None = None,
        min_impact: float | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        signals = self.signals_payload["signals"]
        filtered = []
        for signal in signals:
            if commodity and signal["commodity"] != commodity:
                continue
            if driver and signal["driver"] != driver:
                continue
            if direction and signal["direction"] != direction:
                continue
            if used_in_score is not None and signal["used_in_score"] != used_in_score:
                continue
            if min_impact is not None and signal["impact_score"] < min_impact:
                continue
            filtered.append(signal)
        filtered.sort(key=lambda item: item["date"], reverse=True)
        if limit:
            filtered = filtered[:limit]
        return {
            "generated_at": self.generated_at,
            "refresh_status": self.refresh_status,
            "count": len(filtered),
            "signals": filtered,
        }

    def scenario_payload(self, scenario_input: dict[str, Any]) -> dict[str, Any]:
        commodity_id = scenario_input["commodity"]
        delta = self._scenario_driver_delta(commodity_id, scenario_input)
        commodity = next(
            item
            for item in self.commodities_payload["commodities"]
            if item["id"] == commodity_id
        )
        baseline = self._compute_one(commodity)
        stressed = self._compute_one(commodity, delta)
        impacts = [
            {
                "driver": driver.replace("_", " "),
                "contribution": round(value, 1),
                "direction": "bullish" if value > 0 else "bearish" if value < 0 else "neutral",
                "signals": 0,
            }
            for driver, value in delta.items()
            if value
        ]
        impacts.sort(key=lambda item: abs(item["contribution"]), reverse=True)
        narrative = (
            f"Scenario pushes {COMMODITY_NAMES[commodity_id]} from "
            f"{baseline.overview['risk_score']:.0f} to {stressed.overview['risk_score']:.0f}. "
            f"Main swing factors are "
            f"{', '.join(item['driver'] for item in impacts[:2]) or 'limited changes'}."
        )
        return {
            "commodity": commodity_id,
            "base_risk_score": baseline.overview["risk_score"],
            "new_risk_score": stressed.overview["risk_score"],
            "delta": round(stressed.overview["risk_score"] - baseline.overview["risk_score"], 1),
            "refresh_status": self.refresh_status,
            "recommendation": stressed.detail["recommendation"],
            "driver_impacts": impacts,
            "narrative": narrative,
        }

    def _scenario_driver_delta(
        self,
        commodity_id: str,
        scenario_input: dict[str, Any],
    ) -> dict[str, float]:
        inventory_map = {"low": 8.0, "normal": 0.0, "high": -7.0}
        demand_map = {"weak": -6.0, "neutral": 0.0, "strong": 5.5}
        severity_map = {"none": 0.0, "mild": 6.0, "severe": 13.0}
        tier_map = {"low": -4.0, "medium": 0.0, "high": 6.0}

        energy_weight = DRIVER_WEIGHT_LEVELS[COMMODITY_DRIVER_MAP[commodity_id]["energy"]]
        oil_weight = DRIVER_WEIGHT_LEVELS[COMMODITY_DRIVER_MAP[commodity_id]["oil"]]
        weather_weight = DRIVER_WEIGHT_LEVELS[COMMODITY_DRIVER_MAP[commodity_id]["weather"]]
        geopolitics_weight = DRIVER_WEIGHT_LEVELS[COMMODITY_DRIVER_MAP[commodity_id]["geopolitics"]]
        supply_weight = DRIVER_WEIGHT_LEVELS[COMMODITY_DRIVER_MAP[commodity_id]["supply"]]
        inventories_weight = DRIVER_WEIGHT_LEVELS[COMMODITY_DRIVER_MAP[commodity_id]["inventories"]]
        demand_weight = DRIVER_WEIGHT_LEVELS[COMMODITY_DRIVER_MAP[commodity_id]["demand"]]

        coverage_secured = float(scenario_input["coverage_secured"])
        coverage_offset = -0.05 * coverage_secured

        return {
            "energy": round((scenario_input["energy_cost_shock"] * 0.22 + coverage_offset) * energy_weight, 1),
            "oil": round(scenario_input["oil_shock"] * 0.18 * oil_weight, 1),
            "supply": round(severity_map[scenario_input["supply_disruption"]] * supply_weight, 1),
            "demand": round(demand_map[scenario_input["demand_outlook"]] * demand_weight, 1),
            "inventories": round(inventory_map[scenario_input["inventory_level"]] * inventories_weight, 1),
            "geopolitics": round(tier_map[scenario_input["geopolitical_risk"]] * geopolitics_weight, 1),
            "weather": round(tier_map[scenario_input["weather_risk"]] * weather_weight, 1),
        }
