from __future__ import annotations

import argparse
import json
import os

from backend.app.config import COMMODITIES_SEED_PATH, HISTORICAL_BENCHMARKS_SEED_PATH
from backend.app.historical_benchmarks import build_historical_benchmarks_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build historical benchmark seed data.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Attempt live Cala benchmark history queries before falling back to local seed history.",
    )
    args = parser.parse_args()

    with open(COMMODITIES_SEED_PATH, encoding="utf-8") as handle:
        commodities_payload = json.load(handle)

    payload = build_historical_benchmarks_payload(
        commodities_payload=commodities_payload,
        api_key=os.getenv("CALA_API_KEY"),
        live=args.live,
    )

    HISTORICAL_BENCHMARKS_SEED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORICAL_BENCHMARKS_SEED_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print(f"Wrote {HISTORICAL_BENCHMARKS_SEED_PATH}")
    for item in payload.get("series", []):
        print(
            f"- {item['commodity']}: {item['series_type']} "
            f"({len(item.get('points', []))} points) "
            f"via {item.get('query')}"
        )
        for diagnostic in item.get("diagnostics", []):
            status = diagnostic.get("status")
            rows = diagnostic.get("rows")
            normalized_points = diagnostic.get("normalized_points")
            error = diagnostic.get("error")
            detail = f"rows={rows}, normalized={normalized_points}"
            if error:
                detail += f", error={error}"
            print(f"    {status}: {diagnostic.get('query')} [{detail}]")


if __name__ == "__main__":
    main()
