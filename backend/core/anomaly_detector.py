"""
Anomaly detection using Z-score and IQR methods on historical time series.

Two complementary methods are used because they catch different types of anomalies:
- Z-score works well when data is approximately normally distributed.
- IQR is robust to heavy-tailed distributions and skewed data.

A point is flagged if it breaches EITHER threshold.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ZSCORE_WARNING_THRESHOLD = 2.0   # |z| >= 2 → Warning
ZSCORE_CRITICAL_THRESHOLD = 3.0  # |z| >= 3 → Critical
IQR_MULTIPLIER = 1.5             # Standard IQR fence multiplier


def detect_anomalies(series: pd.Series) -> list[dict]:
    """
    Detect anomalous values in a time series using Z-score and IQR methods.

    We use Z-score rather than simple thresholds because it adapts to the
    scale of each metric — a 1000-unit spike in transaction volume and a
    0.5% spike in default rates both register as anomalies proportional
    to their series variance.

    IQR complements Z-score by catching anomalies in skewed distributions
    where the Z-score is pulled toward the extreme tail.

    Args:
        series: Weekly pd.Series with DatetimeIndex.

    Returns:
        List of dicts with keys: date, value, zscore, iqr_outlier, is_anomaly,
        severity, expected_range (tuple of [low, high]).
    """
    clean = series.dropna()
    if len(clean) < 4:
        return []

    mean = clean.mean()
    std = clean.std()
    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1

    # IQR fences — points outside these are considered outliers
    iqr_lower_fence = q1 - IQR_MULTIPLIER * iqr
    iqr_upper_fence = q3 + IQR_MULTIPLIER * iqr

    # Expected range for display: mean ± 2σ (roughly 95% of a normal distribution)
    expected_low = round(float(mean - 2 * std), 4)
    expected_high = round(float(mean + 2 * std), 4)

    anomalies = []
    for date, value in clean.items():
        zscore = float((value - mean) / std) if std > 0 else 0.0
        abs_z = abs(zscore)
        iqr_outlier = value < iqr_lower_fence or value > iqr_upper_fence

        is_anomaly = abs_z >= ZSCORE_WARNING_THRESHOLD or iqr_outlier

        if not is_anomaly:
            continue

        severity = _classify_severity(abs_z)

        anomalies.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": round(float(value), 4),
            "zscore": round(zscore, 3),
            "iqr_outlier": iqr_outlier,
            "is_anomaly": True,
            "severity": severity,
            "expected_range": [expected_low, expected_high],
        })

    logger.info(
        "Anomaly detection complete: %d anomalies found (%d critical, %d warning)",
        len(anomalies),
        sum(1 for a in anomalies if a["severity"] == "critical"),
        sum(1 for a in anomalies if a["severity"] == "warning"),
    )
    return anomalies


def detect_forward_looking_warnings(
    forecast_rows: list[dict],
    historical_series: pd.Series,
) -> list[dict]:
    """
    Flag forecast periods where the predicted central value exceeds the 95%
    historical band, indicating that the forecast is in uncharted territory.

    These warnings appear in the anomaly panel as 'Forward-Looking Warnings'
    to help users understand where uncertainty is highest.

    Args:
        forecast_rows: List of {date, lower, central, upper} forecast dicts.
        historical_series: Full historical series used to compute the band.

    Returns:
        List of flagged forecast rows with added 'warning_type' key.
    """
    clean = historical_series.dropna()
    if len(clean) < 4:
        return []

    mean = clean.mean()
    std = clean.std()
    band_low = mean - 2 * std
    band_high = mean + 2 * std

    warnings = []
    for row in forecast_rows:
        central = row["central"]
        if central < band_low or central > band_high:
            warnings.append({
                **row,
                "warning_type": "forward_looking",
                "severity": "warning",
                "historical_band": [round(band_low, 4), round(band_high, 4)],
            })

    return warnings


def _classify_severity(abs_zscore: float) -> str:
    """
    Map an absolute Z-score to a severity label.

    Thresholds are calibrated for weekly financial data where short-run
    noise typically stays within 2σ. Anything above 3σ is almost certainly
    a genuine event requiring investigation.

    Args:
        abs_zscore: Absolute value of the Z-score.

    Returns:
        'critical' if >= 3σ, 'warning' if >= 2σ, 'normal' otherwise.
    """
    if abs_zscore >= ZSCORE_CRITICAL_THRESHOLD:
        return "critical"
    elif abs_zscore >= ZSCORE_WARNING_THRESHOLD:
        return "warning"
    return "normal"
