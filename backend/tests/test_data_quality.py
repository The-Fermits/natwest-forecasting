"""
Tests for the data quality pre-flight checker.
"""

import numpy as np
import pandas as pd
import pytest

from core.data_quality import (
    check_missing_values,
    check_data_length,
    check_irregular_intervals,
    check_extreme_outliers,
    run_all_checks,
    has_blocking_failure,
    MIN_PERIODS_FAIL,
)


def make_weekly_series(n: int = 30) -> pd.Series:
    dates = pd.date_range("2023-01-02", periods=n, freq="W-MON")
    return pd.Series([1000.0 + i * 10 for i in range(n)], index=dates, name="value")


def test_detects_missing_values():
    """Series with NaN values is flagged as WARN or FAIL depending on count."""
    series = make_weekly_series(n=30)
    # Inject 5 NaN values (~16.7%)
    series.iloc[5] = np.nan
    series.iloc[10] = np.nan
    series.iloc[15] = np.nan
    series.iloc[20] = np.nan
    series.iloc[25] = np.nan

    result = check_missing_values(series)
    # 5/30 ≈ 16.7% → exceeds 10% WARN threshold → FAIL
    assert result.status == "fail"
    assert "missing" in result.detail.lower()


def test_detects_irregular_intervals():
    """Non-weekly gaps in the time index are flagged as WARN or FAIL."""
    dates = pd.date_range("2023-01-02", periods=20, freq="W-MON").tolist()
    # Replace one date with a +30 day offset to create a gap
    dates[10] = dates[10] + pd.Timedelta(days=30)
    series = pd.Series([1000.0] * 20, index=pd.DatetimeIndex(dates), name="value")

    result = check_irregular_intervals(series)
    assert result.status in ("warn", "fail")


def test_passes_clean_data():
    """All checks pass on a clean, complete weekly series."""
    series = make_weekly_series(n=30)
    checks = run_all_checks(series)

    for check in checks:
        assert check.status == "pass", f"Check '{check.check}' did not pass: {check.detail}"

    assert not has_blocking_failure(checks)


def test_data_length_fail():
    """Series shorter than MIN_PERIODS_FAIL triggers a FAIL status."""
    short_series = make_weekly_series(n=MIN_PERIODS_FAIL - 1)
    result = check_data_length(short_series)
    assert result.status == "fail"


def test_extreme_outliers_flagged():
    """A value exceeding 4σ triggers a WARN status for extreme outliers."""
    series = make_weekly_series(n=52)
    # Inject an extreme outlier at 10x the mean
    series.iloc[25] = series.mean() * 10

    result = check_extreme_outliers(series)
    assert result.status == "warn"
    assert "exceed" in result.detail.lower()
