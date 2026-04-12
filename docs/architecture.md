# System Architecture

## Overview

The NatWest Forecasting Dashboard is a stateless web application with a clear separation 
between the frontend (Next.js) and the backend (FastAPI). All ML computation happens 
server-side. The Claude API key is kept server-side only.

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
│  core/claude_narrator.py  ← Claude API + SSE stream      │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
                       ▼
              Anthropic Claude API
          (claude-sonnet-4-20250514)
```

## Model Selection Logic

```
series length >= 52 weeks?
    YES → autocorrelation at lag 52 > 0.4?
              YES → Prophet (annual seasonality detected)
              NO  → AutoETS (data present but no strong seasonality)
    NO  → AutoETS (insufficient history for Prophet seasonality)
```

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

The `/briefing` endpoint opens an HTTP connection to Claude with `"stream": true`.
As Claude emits content_block_delta events, each token chunk is immediately forwarded
to the browser as a `data: {"token": "..."}` SSE event. The browser's EventSource
API appends each token to the briefing text in real time.

The stream terminates with `data: {"done": true}`.

## Security

- ANTHROPIC_API_KEY: loaded from env var only, never logged or returned to client
- Upload files: written to `data/uploads/<uuid>.csv`, never persisted after session
- CORS: restricted to FRONTEND_URL env var + localhost:3000
- No database, no auth tokens, no persistent user data
