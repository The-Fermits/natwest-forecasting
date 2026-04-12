"""
Tests for the anomaly detector module.
"""

import numpy as np
import pandas as pd
import pytest

from core.anomaly_detector import detect_anomalies, _classify_severity


def make_clean_series(n: int = 52) -> pd.Series:
    """Create a series with no anomalies (values close to mean)."""
    rng = np.random.default_rng(0)
    dates = pd.date_range("2023-01-02", periods=n, freq="W-MON")
    values = 1000.0 + rng.normal(0, 50, n)  # Tight around 1000
    return pd.Series(values, index=dates, name="value")


def make_spiked_series(spike_idx: int = 25, spike_multiplier: float = 5.0) -> pd.Series:
    """Inject an obvious spike at the given index."""
    series = make_clean_series()
    series.iloc[spike_idx] = series.mean() * spike_multiplier
    return series


def test_zscore_flags_spike():
    """An artificially injected 5x spike is detected as an anomaly."""
    series = make_spiked_series(spike_idx=25, spike_multiplier=5.0)
    anomalies = detect_anomalies(series)

    detected_dates = {a["date"] for a in anomalies}
    spike_date = series.index[25].strftime("%Y-%m-%d")

    assert spike_date in detected_dates, "Expected spike was not detected"


def test_no_false_positives_on_clean_data():
    """A truly clean series with tight Gaussian noise has zero anomalies."""
    rng = np.random.default_rng(99)
    dates = pd.date_range("2023-01-02", periods=52, freq="W-MON")
    # Very tight values — all within ±1σ by construction
    values = 1000.0 + rng.uniform(-30, 30, 52)
    series = pd.Series(values, index=dates, name="value")

    anomalies = detect_anomalies(series)
    assert len(anomalies) == 0, f"Unexpected false positives: {anomalies}"


def test_severity_labelling():
    """Severity labels are correctly assigned based on Z-score thresholds."""
    assert _classify_severity(2.5) == "warning"
    assert _classify_severity(3.5) == "critical"
    assert _classify_severity(1.5) == "normal"
    assert _classify_severity(3.0) == "critical"   # Boundary: >= 3 is critical
    assert _classify_severity(2.0) == "warning"    # Boundary: >= 2 is warning
