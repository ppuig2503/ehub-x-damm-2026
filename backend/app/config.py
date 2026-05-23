from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data"
SEEDS_DIR = DATA_DIR / "seeds"
RAW_DIR = DATA_DIR / "raw"
RUNTIME_DIR = DATA_DIR / "runtime"

SIGNALS_SEED_PATH = SEEDS_DIR / "signals.json"
COMMODITIES_SEED_PATH = SEEDS_DIR / "commodities.json"
SCENARIOS_SEED_PATH = SEEDS_DIR / "scenarios.json"
BARLEY_CSV_PATH = RAW_DIR / "ordi_train_public.csv"
RUNTIME_SIGNALS_PATH = RUNTIME_DIR / "signals_latest.json"
REFRESH_LOG_PATH = RUNTIME_DIR / "refresh_log.json"

DEFAULT_GENERATED_AT = "2026-05-23T09:30:00+02:00"

DRIVER_WEIGHT_LEVELS = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.25,
    "none": 0.0,
}

COMMODITY_DRIVER_MAP = {
    "aluminium": {
        "energy": "high",
        "oil": "low",
        "PTA_MEG": "low",
        "weather": "low",
        "regulation": "medium",
        "geopolitics": "high",
        "inventories": "high",
        "imports_exports": "high",
        "futures_prices": "high",
        "demand": "medium",
        "supply": "high",
    },
    "pet": {
        "energy": "medium",
        "oil": "high",
        "PTA_MEG": "high",
        "weather": "low",
        "regulation": "high",
        "geopolitics": "medium",
        "inventories": "medium",
        "imports_exports": "high",
        "futures_prices": "medium",
        "demand": "medium",
        "supply": "medium",
    },
    "energy": {
        "energy": "high",
        "oil": "medium",
        "PTA_MEG": "low",
        "weather": "medium",
        "regulation": "medium",
        "geopolitics": "high",
        "inventories": "high",
        "imports_exports": "medium",
        "futures_prices": "high",
        "demand": "medium",
        "supply": "high",
    },
    "barley": {
        "energy": "low",
        "oil": "low",
        "PTA_MEG": "low",
        "weather": "high",
        "regulation": "medium",
        "geopolitics": "medium",
        "inventories": "high",
        "imports_exports": "high",
        "futures_prices": "medium",
        "demand": "medium",
        "supply": "high",
    },
}

COMMODITY_NAMES = {
    "aluminium": "Aluminium",
    "pet": "PET / vPET / rPET",
    "energy": "Energy",
    "barley": "Barley",
}
