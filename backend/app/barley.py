from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, pstdev
from typing import Iterable


@dataclass
class BarleyPoint:
    date: str
    value: float
    covid_flag: int


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _rolling_mean(values: Iterable[float]) -> float:
    items = list(values)
    return mean(items) if items else 0.0


def _rolling_std(values: Iterable[float]) -> float:
    items = list(values)
    return pstdev(items) if len(items) > 1 else 0.0


def load_barley_points(csv_path: str) -> list[BarleyPoint]:
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [
            BarleyPoint(
                date=row["ds"],
                value=float(row["y"]),
                covid_flag=int(row["covid"]),
            )
            for row in reader
        ]
    rows.sort(key=lambda point: datetime.fromisoformat(point.date))
    return rows


def build_barley_feature_payload(csv_path: str) -> dict[str, object]:
    points = load_barley_points(csv_path)
    values = [point.value for point in points]
    overall_mean = mean(values)
    overall_std = pstdev(values)
    series: list[dict[str, float | int | str]] = []

    for index, point in enumerate(points):
        value = point.value
        trailing_4 = values[max(0, index - 3) : index + 1]
        trailing_12 = values[max(0, index - 11) : index + 1]
        trailing_26 = values[max(0, index - 25) : index + 1]

        prev_4 = values[index - 4] if index >= 4 else value
        prev_12 = values[index - 12] if index >= 12 else value

        momentum_4w = ((value / prev_4) - 1) * 100 if prev_4 else 0.0
        momentum_12w = ((value / prev_12) - 1) * 100 if prev_12 else 0.0
        ma_4 = _rolling_mean(trailing_4)
        ma_12 = _rolling_mean(trailing_12)
        ma_26 = _rolling_mean(trailing_26)
        volatility_12w = (
            (_rolling_std(trailing_12) / ma_12) * 100 if ma_12 else 0.0
        )
        z_score = (value - overall_mean) / overall_std if overall_std else 0.0

        if momentum_4w > 2 and momentum_12w > 4:
            recent_trend = "accelerating_up"
        elif momentum_4w < -2 and momentum_12w < -4:
            recent_trend = "falling"
        else:
            recent_trend = "mixed"

        quantitative_score = clamp(
            50
            + momentum_12w * 0.65
            + momentum_4w * 0.45
            + z_score * 8
            + volatility_12w * 0.3
            + (5 if point.covid_flag else 0),
            0,
            100,
        )

        series.append(
            {
                "date": point.date,
                "value": round(value, 2),
                "covid_flag": point.covid_flag,
                "momentum_4w": round(momentum_4w, 2),
                "momentum_12w": round(momentum_12w, 2),
                "ma_4": round(ma_4, 2),
                "ma_12": round(ma_12, 2),
                "ma_26": round(ma_26, 2),
                "volatility_12w": round(volatility_12w, 2),
                "z_score": round(z_score, 2),
                "recent_trend": recent_trend,
                "quantitative_score": round(quantitative_score, 2),
            }
        )

    latest = series[-1]
    latest_features = {
        "barley_market_indicator": latest["value"],
        "barley_momentum_4w": latest["momentum_4w"],
        "barley_momentum_12w": latest["momentum_12w"],
        "barley_ma_4": latest["ma_4"],
        "barley_ma_12": latest["ma_12"],
        "barley_ma_26": latest["ma_26"],
        "barley_volatility_12w": latest["volatility_12w"],
        "barley_z_score": latest["z_score"],
        "barley_covid_flag": latest["covid_flag"],
        "barley_recent_trend": latest["recent_trend"],
        "barley_quantitative_score": latest["quantitative_score"],
    }

    return {
        "series": series[-52:],
        "latest_features": latest_features,
        "stats": {
            "rows": len(series),
            "start_date": series[0]["date"],
            "end_date": series[-1]["date"],
            "mean": round(overall_mean, 3),
            "min": round(min(values), 3),
            "max": round(max(values), 3),
        },
    }

