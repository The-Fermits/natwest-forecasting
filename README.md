# NatWest AI Predictive Forecasting Dashboard

> Built for NatWest Group "Code for Purpose – India Hackathon" — AI Predictive Forecasting track.

## Overview
A forecasting dashboard for banking operations teams that transforms historical financial
time-series data into actionable predictions. It generates 1–6 week forecasts with
confidence intervals, detects anomalies, compares what-if scenarios, and delivers
plain-English AI briefings — giving risk managers honest signals to act on, not just
backward-looking reports.

**Intended users:** Branch managers, risk officers, and operations analysts at NatWest
who need to anticipate trends in transaction volumes, loan defaults, and customer metrics.

## Features
- [working] Short-term forecasting (1–6 weeks) with Prophet and AutoETS models
- [working] Confidence bands (80% and 95% intervals) on all forecasts
- [working] Baseline model comparison (naive + moving average) with MAPE/RMSE accuracy panel
- [working] Anomaly detection (Z-score + IQR) with severity badges and AI-generated explanations
- [working] Scenario builder: adjust growth rate, remove outliers, apply seasonal boosts
- [working] Side-by-side scenario comparison chart with plain-English diff summary
- [working] Claude AI streaming briefing (non-technical plain-English summary)
- [working] Data quality pre-flight checks with PASS/WARN/FAIL status
- [working] Transparency panel: model used, accuracy, detected patterns
- [working] CSV upload with drag-and-drop and data preview
- [working] Export forecast data as CSV and chart as PNG
- [working] 6 pre-loaded synthetic banking datasets (zero setup required for demo)

## Install and Run

### Prerequisites
- Node.js 18+
- Python 3.11+
- An Anthropic API key (free tier works)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
python data/generate_seed_data.py # Generates default datasets
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local: set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000

## Tech Stack
- **Frontend:** Next.js 14 (TypeScript), Tailwind CSS, Recharts — deployed on Vercel
- **Backend:** Python FastAPI, Pandas, Prophet, statsforecast (AutoETS), SciPy, scikit-learn — deployed on Render.com
- **AI:** Anthropic Claude API (claude-sonnet-4-20250514) for plain-English briefings and anomaly explanations
- **Storage:** Stateless — CSV files for defaults, temporary in-memory processing for uploads

## Architecture

```
Browser (Next.js) ──POST /forecast──► FastAPI Backend
                  ◄── JSON response ──         │
                                               ├─► Prophet / AutoETS
                  ──GET /briefing──────────►   │   (model fit)
                  ◄── SSE token stream ──  Claude API
                                           (AI briefing)
```

See [docs/architecture.md](docs/architecture.md) for full system design.

## Running Tests
```bash
cd backend
pytest tests/ -v
```

## Deployment

### Vercel (Frontend)
1. Push `frontend/` to GitHub.
2. Connect repo to Vercel. Set root directory to `frontend/`.
3. Add environment variable: `NEXT_PUBLIC_API_URL=<your_render_url>`.
4. Deploy.

### Render.com (Backend)
1. Create a new "Web Service" connected to your GitHub repo.
2. Root directory: `backend/`
3. Build command: `pip install -r requirements.txt && python data/generate_seed_data.py`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables: `ANTHROPIC_API_KEY=<your_key>`, `FRONTEND_URL=<your_vercel_url>`
6. Free tier: 512MB RAM, sleeps after 15min inactivity.
7. Add a `/health` route and ping it with UptimeRobot (free) every 5 minutes to prevent sleep.

### CORS
In `main.py`, CORS is pre-configured to allow the `FRONTEND_URL` env var and `localhost:3000`.

## Limitations
- Prophet model has ~2–4 second fit time on first run (Render free tier cold start adds ~30s)
- Upload CSV must have a recognisable date column and a single numeric value column
- Forecasts are univariate — multivariate feature inputs not yet supported

## Future Improvements
- Multivariate forecasting (e.g. include marketing spend as a regressor in Prophet)
- Branch-level drill-down for regional forecasts
- Email alert integration when anomalies are detected in scheduled data refreshes

## License
Apache 2.0 — see [LICENSE](LICENSE)
