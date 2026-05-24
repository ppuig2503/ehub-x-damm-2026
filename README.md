# SmartBuy Signal OS

SmartBuy Signal OS is a local-first procurement cockpit built for the Damm x Engineering HUB Hackathon 2026. It combines Cala-derived market evidence, deterministic scoring, historical benchmark series, and scenario stress testing into a single procurement decision surface.

The app currently covers 4 commodities:
- `aluminium`
- `pet`
- `energy`
- `barley`

All four are now treated through the same product flow:
- live or fallback Cala signals
- benchmark history for charts
- deterministic risk and recommendation engine
- evidence traceability

## What The Product Does

The MVP includes 5 views:
- `Radar` at `/`
- `Commodity Detail` at `/commodity/[id]`
- `Evidence Board` at `/evidence`
- `Scenario Lab` at `/simulator`
- `Action Plan` at `/action-plan`

Backend responsibilities:
- serve overview, detail, evidence, scenario, and action-plan payloads
- refresh normalized signals from Cala
- proxy Cala natural-language search
- build and load one-year monthly benchmark histories

Frontend responsibilities:
- display procurement recommendations and charts
- let users inspect normalized evidence
- run what-if scenarios
- expose live Cala refresh and Cala search

## Current Architecture

- `frontend/`
  Next.js 16 + React 19 + TypeScript
- `backend/`
  FastAPI + Pydantic + deterministic decision engine
- `data/seeds/`
  versioned local source of truth for demo-safe operation
- `data/runtime/`
  live refresh outputs and Cala debug artifacts

Important seed/runtime files:
- [data/seeds/commodities.json](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\data\seeds\commodities.json)
- [data/seeds/signals.json](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\data\seeds\signals.json)
- [data/seeds/scenarios.json](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\data\seeds\scenarios.json)
- [data/seeds/historical_benchmarks.json](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\data\seeds\historical_benchmarks.json)
- [data/runtime/signals_latest.json](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\data\runtime\signals_latest.json)
- [data/runtime/cala_refresh_debug.json](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\data\runtime\cala_refresh_debug.json)

## Tech Stack

### Frontend
- `next@16.2.6`
- `react@19.2.4`
- `react-markdown`
- `remark-gfm`

### Backend
- `fastapi`
- `uvicorn`
- `pydantic`
- `httpx`
- `python-dotenv`

## Requirements

Recommended local setup:
- `Python 3.12`
- `Node.js 20+`
- `npm`

## Installation

From the project root:

```bash
npm install
npm --prefix frontend install
pip install -r backend/requirements.txt
```

## Environment Variables

The backend loads `.env` from the project root.

Minimal useful variables:

```env
CALA_API_KEY=your_key_here
SMARTBUY_API_PORT=8003
SMARTBUY_API_RELOAD=1
SMARTBUY_FORCE_CALA_DEMO=0
```

Notes:
- `CALA_API_KEY` enables real Cala requests.
- `SMARTBUY_FORCE_CALA_DEMO=1` forces a fake successful live refresh using seed data.
- the frontend currently points to `http://127.0.0.1:8003/api/v1` via [frontend/.env.local](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\frontend\.env.local)

## Run Locally

### One command

```bash
npm run dev
```

This starts:
- frontend at [http://localhost:3000](http://localhost:3000)
- backend at [http://127.0.0.1:8003](http://127.0.0.1:8003)

### Run separately

Frontend:

```bash
npm run dev:web
```

Backend:

```bash
npm run dev:api
```

If you want to bypass the helper runner:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8003
```

## Seed Data And Benchmark History

Rebuild the base local seed data:

```bash
npm run seed
```

This recreates:
- commodity seeds
- signal seeds
- scenario catalog
- empty refresh log

### Historical benchmark seeds

Build offline fallback benchmark history:

```bash
python -m backend.scripts.build_historical_benchmarks
```

Build benchmark history from live Cala queries:

```bash
python -m backend.scripts.build_historical_benchmarks --live
```

The benchmark builder currently targets:
- `European aluminium benchmark`
- `Europe PET resin benchmark`
- `EU power benchmark`
- `European feed barley benchmark`

If Cala cannot produce a stable monthly series, the script stores a `local_fallback` history instead.

## Cala Integration

There are 3 Cala-related flows in the project.

### 1. Refresh from Cala

UI action:
- button in Radar

Backend endpoint:
- `POST /api/v1/cala/refresh`

Behavior:
- runs a set of structured Cala queries per commodity and driver
- normalizes results into `Signal[]`
- writes a runtime snapshot to `data/runtime/signals_latest.json`
- writes full query debug output to `data/runtime/cala_refresh_debug.json`

Current refresh states:
- `live`
  Cala responded and runtime signals were rebuilt from that flow
- `fallback`
  Cala was unavailable or failed, so local fallback signals were used
- `seed`
  no runtime refresh exists yet; base seed data is being used

### 2. Cala natural-language search

UI:
- bottom of `Scenario Lab`

Backend endpoint:
- `POST /api/v1/cala/search`

Behavior:
- forwards a natural-language query to Cala search
- returns natural-language content plus optional context, explainability, and entities

### 3. Cala historical benchmark import

Script:
- `python -m backend.scripts.build_historical_benchmarks --live`

Behavior:
- runs benchmark-style monthly price history queries
- normalizes them into exactly 12 monthly points
- persists them into `data/seeds/historical_benchmarks.json`

## API Overview

Main endpoints:
- `GET /api/v1/overview`
- `GET /api/v1/commodities/{commodity_id}`
- `GET /api/v1/signals`
- `GET /api/v1/scenarios/catalog`
- `POST /api/v1/scenarios/evaluate`
- `GET /api/v1/action-plan`
- `POST /api/v1/cala/refresh`
- `POST /api/v1/cala/search`

With the backend running, interactive docs are available at:
- [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs)

## Scoring Model

The project uses a deterministic rule engine, not predictive ML.

High-level flow:
1. Cala or seed rows are normalized into signals.
2. Each signal gets:
   - `direction`
   - `impact_score`
   - `confidence`
   - `used_in_score`
3. Each signal contributes:
   - `direction_sign * impact_score * confidence * driver_weight * 18`
4. Contributions are aggregated by driver and commodity.
5. `risk_score`, `uncertainty_score`, and recommendation are derived from those aggregates plus a proxy score.

Current recommendation outputs:
- `buy`
- `wait`
- `hedge`
- `monitor`

Current operational outputs:
- `suggested_coverage`
- `suggested_horizon`
- recommendation explanation

## Charts

There are 2 different lines in the commodity detail charts:

- `SmartBuy score`
  a heuristic score history reconstructed from current signal strength and normalized benchmark history
- `benchmark`
  the stored market benchmark series for that commodity

Radar cards default to `Score` and allow toggling to `Benchmark` where benchmark history exists.

## Barley Status

`barley` no longer uses its old special CSV-based scoring path.

Current state:
- treated like the other 3 commodities in scoring and UI
- uses Cala/fallback signals like the rest
- uses historical benchmark seed flow like the rest

The raw CSV still exists in:
- [data/raw/ordi_train_public.csv](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\data\raw\ordi_train_public.csv)

But it is no longer the active decision layer.

## Debugging Cala

If a refresh or benchmark import behaves strangely, check these first:

- [data/runtime/cala_refresh_debug.json](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\data\runtime\cala_refresh_debug.json)
  full output of every query in the last refresh, including exact timestamp
- [data/runtime/refresh_log.json](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\data\runtime\refresh_log.json)
  refresh history
- [data/seeds/historical_benchmarks.json](C:\Users\paupr\Desktop\hackathons\Damn-X-EHub_2026\ehub-x-damm-2026\data\seeds\historical_benchmarks.json)
  stored benchmark series and benchmark-import diagnostics

Useful checks:

```bash
python -m backend.scripts.build_historical_benchmarks --live
python -m pytest backend/tests
npm --prefix frontend run lint
npm --prefix frontend run build
```

## Tests

Backend tests:

```bash
npm run test:api
```

Frontend lint:

```bash
npm run lint:web
```

Frontend production build:

```bash
npm run build:web
```

## Project Structure

```text
backend/
  app/
    cala_client.py
    config.py
    data_store.py
    decision_engine.py
    historical_benchmarks.py
    main.py
    models.py
  scripts/
    build_historical_benchmarks.py
    build_seed_data.py
    run_api.py
  tests/

frontend/
  src/
    app/
    components/
    lib/

data/
  raw/
  runtime/
  seeds/
```

## Known Notes

- Cala is still beta and can be slow or inconsistent depending on the query.
- `Refresh from Cala` and historical benchmark import are designed to fall back safely instead of breaking the app.
- There is a stale old backend process on port `8002` in this environment; the current project has been standardized on `8003`.
- Some benchmark series are true Cala benchmark imports and some may still be `local_fallback` depending on the latest successful run.

## Quick Start

```bash
npm install
npm --prefix frontend install
pip install -r backend/requirements.txt
npm run seed
python -m backend.scripts.build_historical_benchmarks --live
npm run dev
```

Then open:
- [http://localhost:3000](http://localhost:3000)
