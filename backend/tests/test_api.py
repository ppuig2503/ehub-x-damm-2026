from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_overview_endpoint():
    response = client.get("/api/v1/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["refresh_status"] in {"seed", "fallback", "live"}
    assert len(payload["commodities"]) == 4


def test_refresh_response_shape():
    response = client.post("/api/v1/cala/refresh", json={})
    assert response.status_code == 200
    payload = response.json()
    assert "query_count" in payload
    assert "duration_seconds" in payload


def test_signals_filter_endpoint():
    response = client.get("/api/v1/signals", params={"commodity": "barley", "limit": 3})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 3
    assert all(signal["commodity"] == "barley" for signal in payload["signals"])


def test_commodity_detail_exposes_history_metadata():
    response = client.get("/api/v1/commodities/aluminium")
    assert response.status_code == 200
    payload = response.json()
    assert payload["history_source"] in {"cala_benchmark", "local_fallback"}
    assert payload["history_label"]
    assert payload["latest_history_value"] > 0


def test_scenario_endpoint():
    response = client.post(
        "/api/v1/scenarios/evaluate",
        json={
            "commodity": "energy",
            "energy_cost_shock": 20,
            "oil_shock": 10,
            "supply_disruption": "mild",
            "demand_outlook": "neutral",
            "inventory_level": "low",
            "geopolitical_risk": "high",
            "weather_risk": "high",
            "coverage_secured": "0",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["new_risk_score"] >= payload["base_risk_score"]
