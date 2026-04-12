"""
Generate synthetic banking time-series seed data for the NatWest Forecasting Dashboard.

Each dataset covers 104 weeks (2 years) starting 2023-01-02, with realistic
patterns including trends, seasonality, noise, and anomalous events.
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
NUM_WEEKS = 104
START_DATE = "2023-01-02"
OUTPUT_DIR = Path(__file__).parent / "defaults"


def build_date_index() -> pd.DatetimeIndex:
    """Build a weekly DatetimeIndex of 104 periods starting 2023-01-02."""
    return pd.date_range(start=START_DATE, periods=NUM_WEEKS, freq="W-MON")


def inject_anomaly(values: np.ndarray, week_index: int, multiplier: float) -> np.ndarray:
    """
    Replace a single week's value with an anomalous spike or dip.

    Args:
        values: Array of values to modify in place.
        week_index: Index position for the anomaly.
        multiplier: Factor applied to the baseline at that point (e.g. 2.5 = 2.5x spike).

    Returns:
        Modified array with the anomaly injected.
    """
    result = values.copy()
    baseline = np.mean(values)
    result[week_index] = baseline * multiplier
    return result


def generate_transaction_volume(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Generate weekly transaction volume data for NatWest branches.

    Pattern: ~12,000/week baseline, +0.5%/week upward trend, slight seasonal
    bumps at start/end of year (quarter-end settlement spikes), Gaussian noise.
    """
    rng = np.random.default_rng(SEED)
    weeks = np.arange(NUM_WEEKS)

    # Upward trend: annualise growth at ~26% over 2 years
    trend = 12_000 * (1 + 0.005) ** weeks

    # Seasonal effect: spikes at weeks 0–4 (Jan) and weeks 50–52 (Dec)
    seasonal = 800 * np.sin(2 * np.pi * weeks / 52)

    noise = rng.normal(0, 800, NUM_WEEKS)
    values = trend + seasonal + noise

    # Quarter-end anomaly spikes (weeks 12, 25, 38, 64)
    for spike_week in [12, 38, 64]:
        values[spike_week] *= 1.55  # ~55% above trend — clear anomaly

    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "value": np.round(values, 2)})


def generate_loan_disbursements(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Generate weekly loan disbursement amounts in GBP.

    Pattern: ~8,500/week baseline, slight upward trend, end-of-month spikes
    every 4th week (weeks 4, 8, 12, ...), Gaussian noise.
    """
    rng = np.random.default_rng(SEED + 1)
    weeks = np.arange(NUM_WEEKS)

    trend = 8_500 * (1 + 0.003) ** weeks
    # End-of-month effect: boosted every 4 weeks
    monthly_boost = np.where(weeks % 4 == 3, 1_200, 0)
    noise = rng.normal(0, 600, NUM_WEEKS)
    values = trend + monthly_boost + noise

    # One large unexpected spike (loan scheme launch)
    values[45] *= 1.60

    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "value": np.round(values, 2)})


def generate_default_rates(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Generate weekly loan default rates as percentages (0–5%).

    Pattern: ~2.1% baseline with mild upward creep, one stress event spike
    to ~3.8% around week 70, Gaussian noise.
    """
    rng = np.random.default_rng(SEED + 2)
    weeks = np.arange(NUM_WEEKS)

    # Slow upward creep to simulate deteriorating credit environment
    trend = 2.1 + weeks * 0.006
    noise = rng.normal(0, 0.15, NUM_WEEKS)
    values = trend + noise

    # Simulate a one-off stress event (e.g. regional economic shock)
    values[70] = 3.8
    values[71] = 3.4  # partial recovery
    values[72] = 3.0  # continuing recovery

    # Clamp to realistic 0–5% range
    values = np.clip(values, 0.1, 5.0)

    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "value": np.round(values, 4)})


def generate_new_signups(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Generate weekly new customer signup counts.

    Pattern: ~340/week baseline, seasonal uplift in January (start-of-year
    financial resolutions) and September (back-to-school / new tax year planning),
    Gaussian noise.
    """
    rng = np.random.default_rng(SEED + 3)
    weeks = np.arange(NUM_WEEKS)

    base = 340.0
    # January spike (weeks 0–3) and September spike (weeks 35–38)
    jan_boost = 80 * np.exp(-0.3 * np.mod(weeks, 52))
    sep_boost = 60 * np.exp(-0.5 * np.abs(np.mod(weeks, 52) - 36))
    seasonal = jan_boost + sep_boost

    noise = rng.normal(0, 25, NUM_WEEKS)
    values = base + seasonal + noise
    values = np.clip(values, 200, 550)

    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "value": np.round(values, 0)})


def generate_churn_rate(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Generate weekly customer churn rate percentages.

    Pattern: ~1.4% baseline with slight downward trend (improving retention
    over 2 years), small Gaussian noise. Realistic for a bank running
    a retention programme.
    """
    rng = np.random.default_rng(SEED + 4)
    weeks = np.arange(NUM_WEEKS)

    # Gradual improvement in retention
    trend = 1.4 - weeks * 0.003
    noise = rng.normal(0, 0.10, NUM_WEEKS)
    values = trend + noise
    values = np.clip(values, 0.3, 2.5)

    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "value": np.round(values, 4)})


def generate_support_tickets(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Generate weekly support ticket volumes.

    Pattern: ~420/week baseline, positively correlated with transaction volume
    spikes (same quarter-end peaks), Gaussian noise.
    """
    rng = np.random.default_rng(SEED + 5)
    weeks = np.arange(NUM_WEEKS)

    base = 420.0
    # Upward trend: more customers = more tickets
    trend = base * (1 + 0.002) ** weeks
    noise = rng.normal(0, 30, NUM_WEEKS)
    values = trend + noise

    # Correlated spike at the same quarter-end weeks as transaction volume
    for spike_week in [12, 38, 64]:
        values[spike_week] *= 1.40

    values = np.clip(values, 200, 900)

    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "value": np.round(values, 0)})


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dates = build_date_index()

    datasets = {
        "transaction_volume": generate_transaction_volume(dates),
        "loan_disbursements": generate_loan_disbursements(dates),
        "default_rates": generate_default_rates(dates),
        "new_signups": generate_new_signups(dates),
        "churn_rate": generate_churn_rate(dates),
        "support_tickets": generate_support_tickets(dates),
    }

    for name, df in datasets.items():
        out_path = OUTPUT_DIR / f"{name}.csv"
        df.to_csv(out_path, index=False)
        print(f"Written {len(df)} rows → {out_path}")  # noqa: T201 — CLI script only


if __name__ == "__main__":
    main()
