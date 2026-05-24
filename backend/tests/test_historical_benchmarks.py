from backend.app.data_store import load_commodities_payload
from backend.app.historical_benchmarks import (
    HISTORY_POINT_COUNT,
    build_seed_history_payload,
    normalize_cala_history_rows,
)


def test_normalize_cala_history_rows_returns_last_twelve_months():
    rows = [
        {"date": f"2025-{month:02d}-15", "value": str(2000 + month * 10)}
        for month in range(1, 13)
    ]

    points = normalize_cala_history_rows(rows)

    assert len(points) == HISTORY_POINT_COUNT
    assert points[0]["date"] == "2025-01-01"
    assert points[-1]["date"] == "2025-12-01"


def test_seed_history_payload_uses_fallback_series_for_non_barley():
    payload = build_seed_history_payload(load_commodities_payload(), "2026-05-01")

    assert len(payload["series"]) == 3
    assert {item["commodity"] for item in payload["series"]} == {"aluminium", "pet", "energy"}
    assert all(item["series_type"] == "local_fallback" for item in payload["series"])
    assert all(len(item["points"]) == HISTORY_POINT_COUNT for item in payload["series"])
