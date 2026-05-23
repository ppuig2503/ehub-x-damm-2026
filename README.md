# SmartBuy Signal OS

SmartBuy Signal OS is a local-first procurement cockpit for the Damm x Engineering HUB Hackathon 2026. It turns normalized market signals plus a real barley dataset into explainable recommendations: `buy`, `wait`, `hedge`, or `monitor`.

## Stack

- `frontend/`: Next.js + TypeScript
- `backend/`: FastAPI + deterministic decision engine
- `data/`: local seeds, barley CSV, and optional runtime refresh snapshots

## Run locally

1. Install the root helper dependency:

```bash
npm install
```

2. Install the Python API dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Rebuild the local seed snapshots:

```bash
npm run seed
```

4. Start frontend and backend together:

```bash
npm run dev
```

Frontend runs on [http://localhost:3000](http://localhost:3000) and the API on [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Cala refresh modes

- Default: fallback to local snapshots
- `SMARTBUY_FORCE_CALA_DEMO=1`: simulate a successful live refresh for the demo flow
- `CALA_API_KEY=...`: attempt a real Cala request before falling back

## Important barley note

`ordi_train_public.csv` is used as a real weekly barley market indicator source. The `y` column is treated as a neutral `barley_market_indicator` proxy until Damm confirms its business meaning and unit.

