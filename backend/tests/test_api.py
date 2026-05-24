from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.cala_client import CalaSearchService

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


def test_compare_evidence_endpoint(monkeypatch):
    async def fake_compare_evidence(self, payload):
        return {
            "query": "organizations.sector=polyethylene terephthalate.oil.date<2026.return(name, date, summary)",
            "count": 1,
            "matches": [
                {
                    "event": "PET resin episode",
                    "date": "2024-05-22",
                    "evidence": "Mock historical comparison",
                    "source_name": "Cala / PET resin episode",
                    "source_url": "https://example.com/mock-source",
                    "source_reference": "Mock Entity",
                }
            ],
        }

    monkeypatch.setattr(CalaSearchService, "compare_evidence", fake_compare_evidence)

    response = client.post(
        "/api/v1/cala/compare-evidence",
        json={
            "query": "organizations.sector=polyethylene terephthalate.oil.date>2025.return(name, date, summary)",
            "commodity": "pet",
            "driver": "oil",
            "event": "Crude remains range-bound with mild upside bias",
            "date": "2026-05-22",
            "region": "Global",
            "evidence": "Oil markets have not broken out, but the floor is firmer than last month.",
            "mechanism": "Oil resilience supports PET cost expectations through upstream feedstocks.",
            "horizon": "2-4 weeks",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "organizations.sector=polyethylene terephthalate.oil.date<2026.return(name, date, summary)"
    assert payload["count"] == 1
    assert payload["matches"][0]["event"] == "PET resin episode"
