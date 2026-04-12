"""
Main forecast endpoint: orchestrates the full forecasting pipeline.

This is the primary endpoint — it runs data quality checks, selects and fits
the model, computes baselines, detects anomalies, and returns a complete
forecast response in a single call.
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.ingestion import load_default_series, load_uploaded_csv
from core.data_quality import run_all_checks, has_blocking_failure
from core.model_selector import select_model, detect_patterns
from core.forecaster import build_forecast
from core.baseline import build_baselines, compute_baseline_accuracy, MOVING_AVERAGE_WINDOW
import numpy as np
from core.anomaly_detector import detect_anomalies
from core.validator import compute_outperformance_pct

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOADS_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"

METRIC_LABELS = {
    "transaction_volume": "Transaction Volume",
    "loan_disbursements": "Loan Disbursements",
    "default_rates": "Default Rates",
    "new_signups": "New Customer Signups",
    "churn_rate": "Customer Churn Rate",
    "support_tickets": "Support Tickets",
}


class ForecastRequest(BaseModel):
    metric: str = Field(..., description="Metric key or 'upload' for user-uploaded data")
    session_id: Optional[str] = Field(None, description="Session UUID from /upload, or null for default data")
    horizon_weeks: int = Field(4, ge=1, le=6, description="Forecast horizon in weeks")
    confidence_level: float = Field(0.80, ge=0.5, le=0.99, description="Confidence interval level")


@router.post("/forecast")
async def run_forecast(request: ForecastRequest) -> dict:
    """
    Run the full forecasting pipeline and return results for the dashboard.

    Pipeline steps:
    1. Load series (default dataset or user upload)
    2. Run pre-flight data quality checks
    3. Check for blocking failures
    4. Select model (Prophet vs AutoETS)
    5. Build forecast with confidence intervals
    6. Build naive + MA baselines
    7. Compute baseline accuracy on hold-out set
    8. Detect anomalies in historical data
    9. Package and return full response

    Args:
        request: ForecastRequest with metric, session_id, horizon, confidence.

    Returns:
        Complete forecast response dict (see API contract in README).

    Raises:
        HTTPException 400: Data quality FAILed or data not found.
        HTTPException 500: Model fitting error.
    """
    # Step 1: Load the time series
    try:
        if request.session_id:
            upload_path = UPLOADS_DIR / f"{request.session_id}.csv"
            if not upload_path.exists():
                raise HTTPException(status_code=400, detail="Upload session not found or expired.")
            series, _ = load_uploaded_csv(upload_path)
            metric_label = "Uploaded Dataset"
        else:
            series = load_default_series(request.metric)
            metric_label = METRIC_LABELS.get(request.metric, request.metric)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Step 2: Pre-flight data quality checks
    quality_checks = run_all_checks(series)
    quality_dicts = [
        {"check": c.check, "status": c.status, "detail": c.detail}
        for c in quality_checks
    ]

    # Step 3: Block forecasting on FAIL
    if has_blocking_failure(quality_checks):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Data quality check failed. Forecasting blocked.",
                "data_quality": quality_dicts,
            },
        )

    # Step 4: Select model
    model_name = select_model(series)
    patterns = detect_patterns(series)

    # Step 5: Build forecast
    try:
        forecast_result = build_forecast(
            series=series,
            horizon_weeks=request.horizon_weeks,
            model_name=model_name,
            confidence_level=request.confidence_level,
        )
    except Exception as exc:
        logger.error("Forecast failed for metric %s: %s", request.metric, exc)
        raise HTTPException(status_code=500, detail=f"Model fitting failed: {exc}") from exc

    # Step 6: Build baselines
    baselines = build_baselines(series, request.horizon_weeks)

    # Step 7: Compute baseline accuracy on hold-out
    # Compute naive and MA values from the training split (without last 4 weeks)
    # to avoid data leakage in hold-out evaluation.
    train_for_baseline = series.iloc[:-4].dropna()
    naive_value = float(train_for_baseline.iloc[-1])
    ma_value = float(train_for_baseline.tail(MOVING_AVERAGE_WINDOW).mean())
    holdout_actuals = series.iloc[-4:]
    baseline_accuracy = compute_baseline_accuracy(
        holdout_actuals=holdout_actuals,
        naive_value=naive_value,
        ma_value=ma_value,
    )

    # Combine model and baseline accuracy
    model_mape = forecast_result["model_accuracy"].get("mape") or 0
    best_baseline_mape = min(
        baseline_accuracy["baseline_naive_mape"],
        baseline_accuracy["baseline_ma_mape"],
    )
    outperformance = compute_outperformance_pct(model_mape, best_baseline_mape)

    accuracy = {
        **forecast_result["model_accuracy"],
        **baseline_accuracy,
        "outperformance_pct": outperformance,
    }

    # Step 8: Detect anomalies
    anomalies = detect_anomalies(series)

    # Step 9: Build historical response
    historical = [
        {"date": date.strftime("%Y-%m-%d"), "value": round(float(val), 4)}
        for date, val in series.items()
        if val is not None and not (val != val)  # filter NaN
    ]

    return {
        "historical": historical,
        "forecast": forecast_result["forecast"],
        "baseline_naive": baselines.naive,
        "baseline_ma": baselines.moving_avg,
        "model_used": model_name,
        "accuracy": accuracy,
        "patterns": patterns,
        "anomalies": anomalies,
        "data_quality": quality_dicts,
        "metric_label": metric_label,
        "training_range": {
            "start": series.index[0].strftime("%Y-%m-%d"),
            "end": series.index[-1].strftime("%Y-%m-%d"),
            "period_count": len(series),
        },
        "confidence_level": request.confidence_level,
    }
