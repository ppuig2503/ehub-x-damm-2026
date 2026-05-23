from backend.app.barley import build_barley_feature_payload
from backend.app.config import BARLEY_CSV_PATH


def test_barley_payload_contains_expected_features():
    payload = build_barley_feature_payload(str(BARLEY_CSV_PATH))
    features = payload["latest_features"]

    assert payload["stats"]["rows"] == 1036
    assert payload["stats"]["start_date"] == "2006-01-01"
    assert payload["stats"]["end_date"] == "2025-11-02"
    assert "barley_quantitative_score" in features
    assert 0 <= features["barley_quantitative_score"] <= 100
    assert features["barley_recent_trend"] in {"accelerating_up", "falling", "mixed"}

