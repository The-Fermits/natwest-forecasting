"""
Naive and moving-average baseline models for forecast comparison.

Baselines are intentionally simple — their purpose is to provide a floor
that the sophisticated model (Prophet / AutoETS) must beat. If the AI model
cannot outperform a naive carry-forward, it is not adding value.
"""

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MOVING_AVERAGE_WINDOW = 4  # 4-week window as specified in the brief


@dataclass
class BaselineForecast:
    """Container for both baseline forecast series."""

    naive: list[dict]      # last-value carry-forward
    moving_avg: list[dict] # rolling mean carry-forward


def build_baselines(historical: pd.Series, horizon_weeks: int) -> BaselineForecast:
    """
    Compute naive and moving-average baseline forecasts for the given horizon.

    Both baselines carry a single constant value forward for the entire horizon
    rather than extrapolating a trend. This is deliberate — it shows a simple
    no-skill reference point that any sensible model should beat.

    Args:
        historical: Weekly pd.Series with DatetimeIndex and float values.
        horizon_weeks: Number of future weekly periods to forecast.

    Returns:
        BaselineForecast with both series as lists of {date, value} dicts.
    """
    last_date = historical.index[-1]
    future_dates = pd.date_range(
        start=last_date + pd.offsets.Week(1),
        periods=horizon_weeks,
        freq="W-MON",
    )

    naive_value = _compute_naive_value(historical)
    ma_value = _compute_moving_average_value(historical)

    logger.info(
        "Baselines computed — naive: %.2f, MA(%d): %.2f",
        naive_value,
        MOVING_AVERAGE_WINDOW,
        ma_value,
    )

    naive_forecast = [
        {"date": d.strftime("%Y-%m-%d"), "value": round(naive_value, 4)}
        for d in future_dates
    ]
    ma_forecast = [
        {"date": d.strftime("%Y-%m-%d"), "value": round(ma_value, 4)}
        for d in future_dates
    ]

    return BaselineForecast(naive=naive_forecast, moving_avg=ma_forecast)


def _compute_naive_value(series: pd.Series) -> float:
    """
    Return the last observed value as the naive forecast.

    The naive carry-forward is the simplest possible model — it says
    "I expect tomorrow to look exactly like today." Most financial
    series will beat this easily, but it is a meaningful lower bound.

    Args:
        series: Historical weekly series.

    Returns:
        The last non-NaN value in the series.
    """
    # Use last valid value in case the final entry is NaN
    return float(series.dropna().iloc[-1])


def _compute_moving_average_value(series: pd.Series) -> float:
    """
    Return the mean of the last MOVING_AVERAGE_WINDOW weeks as the MA forecast.

    A 4-week rolling mean smooths over week-to-week noise without needing
    a full model fit. It is more robust than naive for noisy series.

    Args:
        series: Historical weekly series.

    Returns:
        Mean of the last 4 non-NaN values.
    """
    tail = series.dropna().tail(MOVING_AVERAGE_WINDOW)
    return float(tail.mean())


def compute_baseline_accuracy(
    holdout_actuals: pd.Series,
    naive_value: float,
    ma_value: float,
) -> dict:
    """
    Compute MAPE and RMSE for both baselines on a hold-out set.

    Both baselines are constant (carry-forward), so this measures how well
    a static prediction tracks actual future values.

    Args:
        holdout_actuals: The actual values for the hold-out window.
        naive_value: The naive last-value forecast to evaluate.
        ma_value: The moving-average forecast to evaluate.

    Returns:
        Dict with keys: baseline_naive_mape, baseline_naive_rmse,
                        baseline_ma_mape, baseline_ma_rmse.
    """
    actuals = holdout_actuals.dropna().values

    naive_preds = np.full(len(actuals), naive_value)
    ma_preds = np.full(len(actuals), ma_value)

    naive_mape = _mape(actuals, naive_preds)
    naive_rmse = _rmse(actuals, naive_preds)
    ma_mape = _mape(actuals, ma_preds)
    ma_rmse = _rmse(actuals, ma_preds)

    return {
        "baseline_naive_mape": round(naive_mape, 2),
        "baseline_naive_rmse": round(naive_rmse, 2),
        "baseline_ma_mape": round(ma_mape, 2),
        "baseline_ma_rmse": round(ma_rmse, 2),
    }


def _mape(actuals: np.ndarray, predictions: np.ndarray) -> float:
    """Mean Absolute Percentage Error, skipping zero actuals to avoid division by zero."""
    mask = actuals != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((actuals[mask] - predictions[mask]) / actuals[mask])) * 100)


def _rmse(actuals: np.ndarray, predictions: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(np.mean((actuals - predictions) ** 2)))
