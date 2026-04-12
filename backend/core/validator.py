"""
Hold-out validation and accuracy metric computation.
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

HOLDOUT_WEEKS = 4


def compute_accuracy_metrics(actuals: np.ndarray, predictions: np.ndarray) -> dict:
    """
    Compute MAPE and RMSE between actual and predicted values.

    Args:
        actuals: Array of actual observed values.
        predictions: Array of predicted values, same length.

    Returns:
        Dict with mape (%) and rmse keys.
    """
    mape = _mape(actuals, predictions)
    rmse = _rmse(actuals, predictions)
    return {"mape": round(mape, 2), "rmse": round(rmse, 2)}


def compute_outperformance_pct(model_mape: float, baseline_mape: float) -> float:
    """
    Compute how much the AI model outperforms the best baseline by MAPE.

    Positive value means AI is better. Negative means baseline wins.

    Args:
        model_mape: MAPE of the AI model.
        baseline_mape: MAPE of the baseline (lower of naive/MA).

    Returns:
        Percentage improvement: (baseline_mape - model_mape) / baseline_mape * 100
    """
    if baseline_mape == 0:
        return 0.0
    return round((baseline_mape - model_mape) / baseline_mape * 100, 1)


def _mape(actuals: np.ndarray, predictions: np.ndarray) -> float:
    """Mean Absolute Percentage Error, skipping zero actuals to avoid division by zero."""
    mask = actuals != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((actuals[mask] - predictions[mask]) / actuals[mask])) * 100)


def _rmse(actuals: np.ndarray, predictions: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(np.mean((actuals - predictions) ** 2)))
