"""
Scenario comparison endpoint — applies what-if adjustments to a base forecast.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.scenario_engine import apply_scenario, build_diff_summary

logger = logging.getLogger(__name__)
router = APIRouter()


class SeasonalBoost(BaseModel):
    week: int = Field(..., ge=1, le=6, description="1-indexed week number to boost")
    pct: float = Field(..., ge=-0.5, le=0.5, description="Fractional uplift to apply")


class ScenarioRequest(BaseModel):
    base_forecast: list[dict]
    growth_rate: float = Field(0.0, ge=-0.20, le=0.20, description="Uniform growth adjustment (-20% to +20%)")
    remove_outliers: bool = False
    seasonal_boost: Optional[SeasonalBoost] = None


@router.post("/scenario")
async def run_scenario(request: ScenarioRequest) -> dict:
    """
    Apply scenario adjustments to a base forecast and compute a diff summary.

    Args:
        request: ScenarioRequest with base forecast and adjustment parameters.

    Returns:
        Dict with scenario_forecast and diff_summary.

    Raises:
        HTTPException 400: Empty or invalid base forecast.
    """
    if not request.base_forecast:
        raise HTTPException(status_code=400, detail="base_forecast cannot be empty.")

    scenario_forecast = apply_scenario(
        base_forecast=request.base_forecast,
        growth_rate=request.growth_rate,
        seasonal_boost_week=request.seasonal_boost.week if request.seasonal_boost else None,
        seasonal_boost_pct=request.seasonal_boost.pct if request.seasonal_boost else 0.0,
    )

    diff_summary = build_diff_summary(
        base_forecast=request.base_forecast,
        scenario_forecast=scenario_forecast,
        growth_rate=request.growth_rate,
    )

    return {
        "scenario_forecast": scenario_forecast,
        "diff_summary": diff_summary,
    }
