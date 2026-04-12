"""
Scenario engine: applies user-defined adjustments to a base forecast.

Supports three independent adjustment types that can be combined:
1. Uniform growth rate shift (applied to all periods)
2. Outlier removal before re-fitting (via the forecaster)
3. Seasonal boost on a specific week (point uplift)
"""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def apply_scenario(
    base_forecast: list[dict],
    growth_rate: float = 0.0,
    seasonal_boost_week: Optional[int] = None,
    seasonal_boost_pct: float = 0.0,
) -> list[dict]:
    """
    Apply scenario adjustments to a base forecast to create Scenario B.

    Adjustments are applied in order:
    1. Growth rate shift (multiplies all central/lower/upper values)
    2. Seasonal boost (additional uplift on a specific week index)

    The outlier removal scenario is handled upstream (in the forecast route)
    by re-fitting the model with remove_outliers=True, so it is not applied here.

    Args:
        base_forecast: List of {date, lower, central, upper} dicts.
        growth_rate: Fractional growth rate adjustment (e.g. 0.10 = +10%).
        seasonal_boost_week: 1-indexed week number to apply the boost (1–6).
        seasonal_boost_pct: Fractional uplift for the seasonal boost week.

    Returns:
        Adjusted forecast as a list of {date, lower, central, upper} dicts.
    """
    multiplier = 1.0 + growth_rate
    adjusted = []

    for i, row in enumerate(base_forecast):
        week_number = i + 1  # 1-indexed for user-facing labelling

        # Apply uniform growth adjustment
        lower = row["lower"] * multiplier
        central = row["central"] * multiplier
        upper = row["upper"] * multiplier

        # Apply point-specific seasonal boost on top of growth adjustment
        if seasonal_boost_week is not None and week_number == seasonal_boost_week:
            boost = 1.0 + seasonal_boost_pct
            lower *= boost
            central *= boost
            upper *= boost
            logger.info(
                "Applied seasonal boost of %.1f%% on week %d",
                seasonal_boost_pct * 100,
                week_number,
            )

        adjusted.append({
            "date": row["date"],
            "lower": round(lower, 4),
            "central": round(central, 4),
            "upper": round(upper, 4),
        })

    logger.info(
        "Scenario applied — growth: %.1f%%, seasonal_boost_week: %s, boost_pct: %.1f%%",
        growth_rate * 100,
        seasonal_boost_week,
        seasonal_boost_pct * 100,
    )

    return adjusted


def build_diff_summary(
    base_forecast: list[dict],
    scenario_forecast: list[dict],
    growth_rate: float,
) -> str:
    """
    Generate a plain-English difference summary between base and scenario forecasts.

    This is displayed below the side-by-side scenario comparison chart to give
    non-technical users a quick numerical comparison without reading the chart.

    Args:
        base_forecast: Original forecast rows.
        scenario_forecast: Adjusted scenario forecast rows.
        growth_rate: Growth rate used (for narrative context).

    Returns:
        Human-readable summary string.
    """
    if not base_forecast or not scenario_forecast:
        return "No forecast data available for comparison."

    # Use the week with the largest absolute difference as the headline
    max_diff_idx = 0
    max_diff = 0.0
    for i, (base_row, scen_row) in enumerate(zip(base_forecast, scenario_forecast)):
        diff = abs(scen_row["central"] - base_row["central"])
        if diff > max_diff:
            max_diff = diff
            max_diff_idx = i

    headline_week = max_diff_idx + 1
    base_val = base_forecast[max_diff_idx]["central"]
    scen_val = scenario_forecast[max_diff_idx]["central"]
    scen_low = scenario_forecast[max_diff_idx]["lower"]
    scen_high = scenario_forecast[max_diff_idx]["upper"]

    growth_label = f"+{growth_rate * 100:.0f}%" if growth_rate >= 0 else f"{growth_rate * 100:.0f}%"

    return (
        f"Under the {growth_label} growth scenario, Week {headline_week} is expected to reach "
        f"{scen_val:,.0f} (vs {base_val:,.0f} in the baseline). "
        f"Range: {scen_low:,.0f}–{scen_high:,.0f}."
    )
