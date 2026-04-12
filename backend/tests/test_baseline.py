"""
Tests for the baseline model module.
"""

import numpy as np
import pandas as pd
import pytest

from core.baseline import (
    build_baselines,
    _compute_naive_value,
    _compute_moving_average_value,
    MOVING_AVERAGE_WINDOW,
)


def make_series(n: int = 20, last_value: float = 500.0) -> pd.Series:
    dates = pd.date_range("2023-01-02", periods=n, freq="W-MON")
    values = [100.0 * (i + 1) for i in range(n - 1)] + [last_value]
    return pd.Series(values, index=dates, name="value")


def test_naive_baseline_equals_last_value():
    """Naive baseline carries the last observed value forward for all periods."""
    series = make_series(last_value=777.0)
    last_val = float(series.iloc[-1])

    baselines = build_baselines(series, horizon_weeks=4)

    for row in baselines.naive:
        assert row["value"] == pytest.approx(last_val, rel=1e-4)


def test_moving_average_window():
    """Moving average uses the last MOVING_AVERAGE_WINDOW (4) observations."""
    # Craft a series where the last 4 values have a known mean
    n = 20
    dates = pd.date_range("2023-01-02", periods=n, freq="W-MON")
    values = [1000.0] * 16 + [200.0, 300.0, 400.0, 500.0]  # Last 4 avg = 350
    series = pd.Series(values, index=dates, name="value")

    ma_value = _compute_moving_average_value(series)
    expected = np.mean([200.0, 300.0, 400.0, 500.0])

    assert ma_value == pytest.approx(expected, rel=1e-6)
