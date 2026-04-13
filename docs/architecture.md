# System Architecture

## Overview

The NatWest Forecasting Dashboard is a stateless web application with a clear separation 
between the frontend (Next.js) and the backend (FastAPI). All ML computation happens 
server-side. The Gemini API key is kept server-side only.

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (Next.js)                    │
│  Landing Page → Dashboard → Components                   │
│  Recharts charts, SSE EventSource, CSV drag-drop         │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS REST + SSE
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                         │
│  POST /forecast  POST /upload  POST /scenario            │
│  POST /anomaly   GET /briefing (SSE)  GET /health        │
│                                                          │
│  core/ingestion.py      ← CSV parse, resample            │
│  core/data_quality.py   ← Pre-flight checks              │
│  core/model_selector.py ← Prophet vs AutoETS             │
│  core/forecaster.py     ← Model fit + intervals          │
│  core/baseline.py       ← Naive + MA comparison          │
│  core/anomaly_detector.py ← Z-score + IQR               │
│  core/scenario_engine.py  ← What-if adjustments          │
│  core/gemini_narrator.py  ← Gemini API + SSE stream      │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
                       ▼
               Google Gemini API
               (gemini-1.5-flash)
```

## Model Selection Logic

We prioritize giving the user the best possible model while ensuring the application never crashes due to environment constraints:

1. **Model Selection**: The system uses a heuristic to choose between **Prophet** (for long, seasonal series) and **AutoETS** (for shorter series).
2. **Stability Mode**: On Windows environments where C++ compilers for Prophet/Stan might be missing, the backend detects the failure and automatically falls back to **AutoETS**. This ensures 100% uptime for the dashboard.
3. **Reasoning**: AutoETS is significantly more robust and requires zero external system dependencies, making it the perfect fail-safe for a distributed banking dashboard.

## Forecasting Pipeline (per /forecast request)

1. Load series (default CSV or uploaded session file)
2. Run 4 pre-flight data quality checks
3. Block request if any check returns FAIL
4. Auto-select Prophet or AutoETS
5. Fit model on full series → generate horizon_weeks forecast rows with CI
6. Refit on train split (last 4 weeks held out) → compute MAPE, RMSE
7. Compute naive + MA(4) baselines on same hold-out → compare accuracy
8. Detect Z-score and IQR anomalies in historical data
9. Return all results as a single JSON response

## SSE Streaming (/briefing)

The `/briefing` endpoint opens an HTTP connection to Google Gemini.
As Gemini emits streaming JSON chunks, each token is immediately forwarded
to the browser as a `data: {"token": "..."}` SSE event. The browser's EventSource
API appends each token to the briefing text in real time.

The stream terminates with `data: {"done": true}`.

## Security

- GEMINI_API_KEY: loaded from env var only, never logged or returned to client
- Upload files: written to `data/uploads/<uuid>.csv`, never persisted after session
- CORS: restricted to FRONTEND_URL env var + localhost:3000
- No database, no auth tokens, no persistent user data
