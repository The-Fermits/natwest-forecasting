"""
Tests for the forecaster module (Prophet + AutoETS).
"""

import pandas as pd
import pytest

from core.forecaster import build_forecast


def make_series(n_weeks: int = 60, start: str = "2023-01-02") -> pd.Series:
    """Create a realistic-looking weekly series for testing."""
    import numpy as np
    rng = np.random.default_rng(42)
    dates = pd.date_range(start, periods=n_weeks, freq="W-MON")
    values = 10_000 + rng.normal(0, 500, n_weeks) + [i * 10 for i in range(n_weeks)]
    return pd.Series(values, index=dates, name="value", dtype=float)


@pytest.mark.parametrize("model_name", ["Prophet", "AutoETS"])
def test_prophet_forecast_length(model_name):
    """Forecast output has exactly horizon_weeks rows."""
    series = make_series(n_weeks=60)
    horizon = 4
    result = build_forecast(series, horizon_weeks=horizon, model_name=model_name)
    assert len(result["forecast"]) == horizon


@pytest.mark.parametrize("model_name", ["Prophet", "AutoETS"])
def test_confidence_intervals_ordered(model_name):
    """Lower bound ≤ central estimate ≤ upper bound for every forecast row."""
    series = make_series(n_weeks=60)
    result = build_forecast(series, horizon_weeks=4, model_name=model_name)

    for row in result["forecast"]:
        assert row["lower"] <= row["central"], f"lower > central: {row}"
        assert row["central"] <= row["upper"], f"central > upper: {row}"


def test_autoets_fallback():
    """AutoETS is used directly when specified (and works with short series)."""
    short_series = make_series(n_weeks=24)
    result = build_forecast(short_series, horizon_weeks=4, model_name="AutoETS")
    assert len(result["forecast"]) == 4


def test_forecast_returns_dates():
    """Forecast dates are weekly, starting the week after the training end date."""
    series = make_series(n_weeks=60)
    result = build_forecast(series, horizon_weeks=3, model_name="AutoETS")

    forecast_dates = pd.to_datetime([row["date"] for row in result["forecast"]])
    last_train_date = series.index[-1]

    # Each forecast date should be >= 1 week after the last training date
    assert all(d > last_train_date for d in forecast_dates)

    # Dates should be in ascending order
    assert list(forecast_dates) == sorted(forecast_dates)
