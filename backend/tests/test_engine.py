from backend.app.data_store import load_commodities_payload, load_seed_signals_payload
from backend.app.decision_engine import SmartBuyEngine


def build_engine():
    signals_payload = load_seed_signals_payload()
    commodities_payload = load_commodities_payload()
    return SmartBuyEngine(
        commodities_payload=commodities_payload,
        signals_payload=signals_payload,
        generated_at=signals_payload["generated_at"],
        refresh_status=signals_payload["refresh_status"],
    )


def test_overview_contains_four_commodities():
    payload = build_engine().overview_payload()
    assert len(payload["commodities"]) == 4
    assert payload["market_status"] in {"Stable", "Watch", "High Risk"}


def test_risk_order_matches_demo_story():
    payload = build_engine().overview_payload()
    ordered_ids = [item["id"] for item in payload["commodities"]]
    assert ordered_ids[0] in {"aluminium", "energy"}
    assert "barley" in ordered_ids


def test_scenario_evaluation_changes_score():
    engine = build_engine()
    result = engine.scenario_payload(
        {
            "commodity": "aluminium",
            "energy_cost_shock": 15,
            "oil_shock": 0,
            "supply_disruption": "severe",
            "demand_outlook": "neutral",
            "inventory_level": "low",
            "geopolitical_risk": "high",
            "weather_risk": "medium",
            "coverage_secured": "25",
        }
    )
    assert result["new_risk_score"] > result["base_risk_score"]
    assert result["recommendation"]["recommended_action"] in {"buy", "hedge", "monitor", "wait"}

