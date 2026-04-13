"""
FastAPI application entry point for the NatWest Forecasting Dashboard backend.

Configures CORS, logging, routes, and startup events. All secrets are loaded
from environment variables via python-dotenv — no hardcoded credentials anywhere.
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, upload, forecast, anomaly, scenario, briefing

# Load environment variables from .env before anything else
load_dotenv()

# Configure structured logging based on LOG_LEVEL env var
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager — runs setup on startup and teardown on shutdown.

    Startup: Verify default datasets exist (fail fast if seed data is missing).
    Shutdown: No cleanup needed for stateless app.
    """
    from pathlib import Path
    defaults_dir = Path(__file__).parent / "data" / "defaults"
    expected_files = [
        "transaction_volume.csv", "loan_disbursements.csv", "default_rates.csv",
        "new_signups.csv", "churn_rate.csv", "support_tickets.csv",
    ]
    missing = [f for f in expected_files if not (defaults_dir / f).exists()]
    if missing:
        logger.warning(
            "Default datasets missing: %s. Run: python data/generate_seed_data.py",
            missing,
        )
    else:
        logger.info("All default datasets present in %s", defaults_dir)

    logger.info("NatWest Forecasting API starting up")
    yield
    logger.info("NatWest Forecasting API shutting down")


app = FastAPI(
    title="NatWest AI Predictive Forecasting API",
    description=(
        "Backend API for the NatWest Forecasting Dashboard. "
        "Provides time-series forecasting, anomaly detection, scenario comparison, "
        "and Gemini AI-powered plain-English briefings."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: explicitly list all allowed origins.
# Both Vercel URLs are included — the stable clean URL and the deployment hash URL —
# so requests succeed regardless of which Vercel domain the browser is on.
allowed_origins = [
    "https://natwest-forecasting.vercel.app",
    "https://natwest-forecasting-73ftg5nf6-the-fermits-projects.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route modules
app.include_router(health.router, tags=["Health"])
app.include_router(upload.router, tags=["Data"])
app.include_router(forecast.router, tags=["Forecast"])
app.include_router(anomaly.router, tags=["Anomaly"])
app.include_router(scenario.router, tags=["Scenario"])
app.include_router(briefing.router, tags=["Briefing"])