"""
Model selection logic: decides whether to use Prophet or AutoETS for a given series.

The selection is based on data length and detected seasonality strength.
Prophet is more powerful but slower; AutoETS is faster and more robust on
shorter or non-seasonal series.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Prophet requires at least one full year to detect annual seasonality reliably
PROPHET_MIN_PERIODS = 52
# Autocorrelation at lag 52 above this threshold signals strong annual seasonality
SEASONALITY_ACF_THRESHOLD = 0.4
# Lag to check for annual seasonality in weekly data
ANNUAL_LAG = 52


def select_model(series: pd.Series) -> str:
    """
    Choose between 'Prophet' and 'AutoETS' based on series characteristics.

    Decision rules:
    - Use Prophet if: len >= 52 AND autocorrelation at lag 52 > 0.4
    - Use AutoETS otherwise: shorter series or weak seasonality

    We prefer AutoETS for short series because Prophet's seasonality
    decomposition becomes unreliable when the training window is shorter
    than one full seasonal cycle.

    Args:
        series: Weekly pd.Series with DatetimeIndex.

    Returns:
        Model name string: 'Prophet' or 'AutoETS'.
    """
    n = len(series)

    if n < PROPHET_MIN_PERIODS:
        logger.info(
            "Selecting AutoETS: only %d periods (need >= %d for Prophet)", n, PROPHET_MIN_PERIODS
        )
        return "AutoETS"

    acf_at_annual_lag = _compute_autocorrelation(series, lag=ANNUAL_LAG)
    logger.info("Autocorrelation at lag %d: %.3f", ANNUAL_LAG, acf_at_annual_lag)

    if acf_at_annual_lag > SEASONALITY_ACF_THRESHOLD:
        logger.info(
            "Selecting Prophet: strong annual seasonality detected (ACF=%.3f > %.1f)",
            acf_at_annual_lag,
            SEASONALITY_ACF_THRESHOLD,
        )
        return "Prophet"

    logger.info(
        "Selecting AutoETS: weak seasonality (ACF=%.3f <= %.1f)",
        acf_at_annual_lag,
        SEASONALITY_ACF_THRESHOLD,
    )
    return "AutoETS"


def detect_patterns(series: pd.Series) -> dict:
    """
    Summarise the key time-series patterns for display in the transparency panel.

    Patterns are computed on the full series (including training + validation)
    so the user sees characteristics of all their data, not just the training set.

    Args:
        series: Weekly pd.Series with DatetimeIndex.

    Returns:
        Dict with keys: trend, seasonality_period, seasonality_strength.
    """
    trend_direction = _detect_trend(series)
    acf_annual = _compute_autocorrelation(series, lag=ANNUAL_LAG)

    seasonality_period = ANNUAL_LAG if acf_annual > 0.3 else None
    seasonality_strength = round(float(acf_annual), 3) if acf_annual > 0.3 else None

    return {
        "trend": trend_direction,
        "seasonality_period": seasonality_period,
        "seasonality_strength": seasonality_strength,
    }


def _compute_autocorrelation(series: pd.Series, lag: int) -> float:
    """
    Compute Pearson autocorrelation of the series with itself shifted by lag periods.

    Using raw Pearson correlation rather than the statsmodels ACF function
    avoids an extra dependency and is sufficient for the binary switch decision
    we need here.

    Args:
        series: Time series.
        lag: Number of periods to shift.

    Returns:
        Pearson correlation coefficient in [-1, 1]. Returns 0.0 if insufficient data.
    """
    clean = series.dropna()
    if len(clean) <= lag:
        return 0.0

    original = clean.iloc[lag:].values
    lagged = clean.iloc[:-lag].values

    if np.std(original) == 0 or np.std(lagged) == 0:
        return 0.0

    correlation = float(np.corrcoef(original, lagged)[0, 1])
    # Guard against NaN from perfectly constant windows
    return correlation if not np.isnan(correlation) else 0.0


def _detect_trend(series: pd.Series) -> str:
    """
    Classify the overall trend direction using linear regression slope.

    We normalise by the series mean so the slope is interpretable as a
    percentage change per period, which is consistent across different
    metric scales (e.g. comparing 0–5% default rates to 12,000 transactions).

    Args:
        series: Weekly time series.

    Returns:
        One of: 'upward', 'downward', 'flat'.
    """
    clean = series.dropna()
    x = np.arange(len(clean))
    slope = float(np.polyfit(x, clean.values, deg=1)[0])

    # Normalise slope against the series mean to get a relative gradient
    relative_slope = slope / (clean.mean() + 1e-9)

    if relative_slope > 0.001:
        return "upward"
    elif relative_slope < -0.001:
        return "downward"
    else:
        return "flat"
