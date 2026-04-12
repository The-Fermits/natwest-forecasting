"""
Pre-flight data quality checks run before any forecasting model is fitted.

Each check returns a status of PASS, WARN, or FAIL along with a human-readable
detail message. A FAIL status blocks forecasting to prevent misleading outputs.
A WARN status allows forecasting but attaches a disclaimer to results.
"""

import logging
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

Status = Literal["pass", "warn", "fail"]

MIN_PERIODS_FAIL = 12   # Fewer than this → FAIL
MIN_PERIODS_WARN = 24   # Fewer than this → WARN
EXTREME_OUTLIER_SIGMA = 4.0   # Z-score threshold for extreme outlier warning
IRREGULAR_INTERVAL_DAYS = 7   # Expected interval between weekly observations


@dataclass
class QualityCheck:
    """Result of a single pre-flight data quality check."""

    check: str
    status: Status
    detail: str


def run_all_checks(series: pd.Series) -> list[QualityCheck]:
    """
    Run the full pre-flight checklist on a weekly time series.

    Checks are independent and all run even if some fail, so the UI can
    show the full picture without stopping at the first problem.

    Args:
        series: Weekly pd.Series with DatetimeIndex.

    Returns:
        List of QualityCheck results, one per check category.
    """
    checks = [
        check_missing_values(series),
        check_data_length(series),
        check_irregular_intervals(series),
        check_extreme_outliers(series),
    ]

    fail_count = sum(1 for c in checks if c.status == "fail")
    warn_count = sum(1 for c in checks if c.status == "warn")
    logger.info(
        "Pre-flight complete: %d FAIL, %d WARN, %d PASS",
        fail_count,
        warn_count,
        len(checks) - fail_count - warn_count,
    )
    return checks


def check_missing_values(series: pd.Series) -> QualityCheck:
    """
    Count NaN values in the series after interpolation has been attempted.

    We check post-interpolation because the ingestion module already fills
    isolated gaps. Remaining NaNs indicate structural data problems
    (e.g. trailing NaNs from resampling).

    Args:
        series: Weekly time series.

    Returns:
        PASS if no missing values, WARN if ≤10%, FAIL if >10% missing.
    """
    missing_count = int(series.isna().sum())
    missing_pct = missing_count / len(series) * 100

    if missing_count == 0:
        return QualityCheck("missing_values", "pass", "0 missing values")
    elif missing_pct <= 10:
        return QualityCheck(
            "missing_values",
            "warn",
            f"{missing_count} missing values ({missing_pct:.1f}%) — interpolated",
        )
    else:
        return QualityCheck(
            "missing_values",
            "fail",
            f"{missing_count} missing values ({missing_pct:.1f}%) — too many to interpolate reliably",
        )


def check_data_length(series: pd.Series) -> QualityCheck:
    """
    Verify the series has sufficient length for reliable forecasting.

    Models need enough history to learn seasonal patterns. Fewer than 12
    periods provides no meaningful signal for a prediction interval.

    Args:
        series: Weekly time series.

    Returns:
        FAIL if < 12 periods, WARN if 12–23 periods, PASS if ≥ 24 periods.
    """
    n = len(series)

    if n < MIN_PERIODS_FAIL:
        return QualityCheck(
            "data_length",
            "fail",
            f"Only {n} weekly periods — minimum {MIN_PERIODS_FAIL} required to run any model",
        )
    elif n < MIN_PERIODS_WARN:
        return QualityCheck(
            "data_length",
            "warn",
            f"{n} weekly periods — forecasts may be unreliable below {MIN_PERIODS_WARN} periods",
        )
    else:
        return QualityCheck("data_length", "pass", f"{n} weekly periods")


def check_irregular_intervals(series: pd.Series) -> QualityCheck:
    """
    Detect gaps in the time index that are wider than the expected 7-day interval.

    Gaps cause models to misinterpret seasonality because they assume evenly
    spaced observations. We flag any gap > 8 days as irregular.

    Args:
        series: Weekly pd.Series with DatetimeIndex.

    Returns:
        PASS if all intervals are ≤ 8 days, WARN if ≤ 5 gaps, FAIL if > 5 gaps.
    """
    if len(series) < 2:
        return QualityCheck("irregular_intervals", "pass", "Insufficient data to check intervals")

    intervals = series.index.to_series().diff().dropna()
    irregular = intervals[intervals > pd.Timedelta(days=IRREGULAR_INTERVAL_DAYS + 1)]
    gap_count = len(irregular)

    if gap_count == 0:
        return QualityCheck(
            "irregular_intervals", "pass", f"All intervals {IRREGULAR_INTERVAL_DAYS} days"
        )
    elif gap_count <= 5:
        return QualityCheck(
            "irregular_intervals",
            "warn",
            f"{gap_count} irregular interval(s) detected — seasonality estimates may be affected",
        )
    else:
        return QualityCheck(
            "irregular_intervals",
            "fail",
            f"{gap_count} irregular intervals — data appears too fragmented for reliable forecasting",
        )


def check_extreme_outliers(series: pd.Series) -> QualityCheck:
    """
    Flag data points that exceed 4 standard deviations from the mean.

    Points above 4σ are so extreme that they are almost certainly data entry
    errors rather than genuine events. We warn rather than fail because
    the anomaly detector will catch them during analysis.

    Args:
        series: Weekly time series with numeric values.

    Returns:
        PASS if none, WARN if any point exceeds 4σ.
    """
    clean = series.dropna()
    if len(clean) < 4:
        return QualityCheck("extreme_outliers", "pass", "Too few points to assess outliers")

    mean = clean.mean()
    std = clean.std()

    if std == 0:
        return QualityCheck("extreme_outliers", "pass", "Constant series — no outliers possible")

    zscores = np.abs((clean - mean) / std)
    extreme_count = int((zscores > EXTREME_OUTLIER_SIGMA).sum())

    if extreme_count == 0:
        return QualityCheck("extreme_outliers", "pass", f"No points exceed {EXTREME_OUTLIER_SIGMA}σ")
    else:
        return QualityCheck(
            "extreme_outliers",
            "warn",
            f"{extreme_count} point(s) exceed {EXTREME_OUTLIER_SIGMA}σ — recommend manual review before forecasting",
        )


def has_blocking_failure(checks: list[QualityCheck]) -> bool:
    """
    Return True if any check has FAIL status, which blocks forecasting.

    Args:
        checks: List of QualityCheck results from run_all_checks.

    Returns:
        True if forecasting should be blocked.
    """
    return any(c.status == "fail" for c in checks)
