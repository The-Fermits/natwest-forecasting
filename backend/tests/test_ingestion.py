"""
Tests for the CSV ingestion module.
"""

import io
from pathlib import Path

import pandas as pd
import pytest

from core.ingestion import (
    load_default_series,
    load_uploaded_csv,
    _detect_date_column,
    _detect_value_column,
    MIN_PERIODS,
)


def make_weekly_csv(n_weeks: int = 20, date_col: str = "date", value_col: str = "value") -> Path:
    """Helper: write a temporary weekly CSV to /tmp for tests."""
    dates = pd.date_range("2023-01-02", periods=n_weeks, freq="W-MON").strftime("%Y-%m-%d")
    df = pd.DataFrame({date_col: dates, value_col: range(1000, 1000 + n_weeks)})
    tmp_path = Path("/tmp") / "test_upload.csv"
    df.to_csv(tmp_path, index=False)
    return tmp_path


def test_parse_valid_csv_weekly():
    """Valid weekly CSV parses into a Series with the expected length."""
    csv_path = make_weekly_csv(n_weeks=20)
    series, metadata = load_uploaded_csv(csv_path)

    assert isinstance(series, pd.Series)
    assert len(series) == 20
    assert series.dtype == float or pd.api.types.is_numeric_dtype(series)


def test_parse_detects_date_column():
    """Auto-detection finds the date column by name hinting."""
    df = pd.DataFrame({
        "week": pd.date_range("2023-01-02", periods=15, freq="W-MON").strftime("%Y-%m-%d"),
        "amount": range(100, 115),
    })
    detected = _detect_date_column(df)
    assert detected == "week"


def test_resample_to_weekly():
    """Daily data is correctly resampled to weekly frequency."""
    # Generate daily data covering 15 weeks
    daily_dates = pd.date_range("2023-01-02", periods=15 * 7, freq="D").strftime("%Y-%m-%d")
    df = pd.DataFrame({"date": daily_dates, "value": [100.0] * (15 * 7)})
    tmp_path = Path("/tmp") / "test_daily.csv"
    df.to_csv(tmp_path, index=False)

    series, metadata = load_uploaded_csv(tmp_path)

    # After weekly resampling, should have roughly 15 weeks
    assert 13 <= len(series) <= 17
    assert metadata["frequency"] == "W"


def test_minimum_length_validation():
    """CSV with fewer than MIN_PERIODS weeks raises ValueError."""
    csv_path = make_weekly_csv(n_weeks=MIN_PERIODS - 1)

    with pytest.raises(ValueError, match="Minimum required"):
        load_uploaded_csv(csv_path)


def test_handles_missing_values():
    """Missing values in the series are interpolated, not left as NaN."""
    dates = pd.date_range("2023-01-02", periods=20, freq="W-MON").strftime("%Y-%m-%d")
    values = [float(i * 100) for i in range(20)]
    values[5] = None   # Inject a missing value
    values[10] = None  # Inject a second missing value

    df = pd.DataFrame({"date": dates, "value": values})
    tmp_path = Path("/tmp") / "test_missing.csv"
    df.to_csv(tmp_path, index=False)

    series, _ = load_uploaded_csv(tmp_path)

    # After interpolation there should be no NaN values
    assert series.isna().sum() == 0
