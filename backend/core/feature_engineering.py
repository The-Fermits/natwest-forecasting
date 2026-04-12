"""
Feature engineering: lag features and rolling statistics for richer model inputs.
"""

import pandas as pd
import numpy as np


def add_lag_features(series: pd.Series, lags: list[int] = [1, 4, 52]) -> pd.DataFrame:
    """
    Add lag features to a series for use in feature-based models.

    Lags capture autocorrelation at different horizons:
    - Lag 1: last-week persistence (short-term momentum)
    - Lag 4: one-month lag (monthly seasonality)
    - Lag 52: same week last year (annual seasonality)

    Args:
        series: Weekly pd.Series with DatetimeIndex.
        lags: List of lag periods to compute.

    Returns:
        DataFrame with original value plus lag columns.
    """
    df = series.rename("value").to_frame()
    for lag in lags:
        df[f"lag_{lag}"] = df["value"].shift(lag)
    return df


def add_rolling_statistics(series: pd.Series, windows: list[int] = [4, 12]) -> pd.DataFrame:
    """
    Compute rolling mean and standard deviation for the given window sizes.

    Rolling statistics help models detect local trends and volatility regimes
    without requiring explicit change-point detection.

    Args:
        series: Weekly pd.Series with DatetimeIndex.
        windows: List of rolling window sizes in weeks.

    Returns:
        DataFrame with rolling mean and std columns.
    """
    df = series.rename("value").to_frame()
    for window in windows:
        df[f"rolling_mean_{window}"] = df["value"].rolling(window).mean()
        df[f"rolling_std_{window}"] = df["value"].rolling(window).std()
    return df
