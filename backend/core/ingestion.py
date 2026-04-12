"""
CSV ingestion, date detection, resampling, and validation for the forecast pipeline.

This module is the entry point for all data — both default datasets and user uploads.
It normalises every input to a weekly pd.Series with a DatetimeIndex before
handing off to the forecasting modules.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Minimum observations required to run any model
MIN_PERIODS = 12
# Patterns that suggest a column is a date column, ordered by specificity
DATE_COLUMN_HINTS = ["date", "week", "period", "time", "timestamp", "ds"]
# Patterns that suggest a column is the value column
VALUE_COLUMN_HINTS = ["value", "amount", "volume", "count", "rate", "qty", "quantity", "total"]

DEFAULTS_DIR = Path(__file__).parent.parent / "data" / "defaults"


def load_default_series(metric: str) -> pd.Series:
    """
    Load one of the pre-seeded default banking datasets by metric name.

    Args:
        metric: One of the 6 built-in metric identifiers (e.g. 'transaction_volume').

    Returns:
        Weekly pd.Series with DatetimeIndex and float values.

    Raises:
        FileNotFoundError: If the metric CSV does not exist in the defaults directory.
        ValueError: If the CSV cannot be parsed into a valid time series.
    """
    csv_path = DEFAULTS_DIR / f"{metric}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Default dataset not found: {csv_path}")

    logger.info("Loading default dataset: %s", metric)
    df = pd.read_csv(csv_path)
    return _dataframe_to_series(df, source_label=metric)


def load_uploaded_csv(file_path: Path) -> tuple[pd.Series, dict]:
    """
    Parse a user-uploaded CSV file into a normalised weekly time series.

    Auto-detects the date and value columns by name matching and falls back
    to positional detection (first parseable date column, first numeric column).

    Args:
        file_path: Absolute path to the uploaded CSV.

    Returns:
        Tuple of (weekly Series, metadata dict with detected column names and stats).

    Raises:
        ValueError: If date/value columns cannot be identified or data is invalid.
    """
    logger.info("Loading uploaded CSV: %s", file_path)
    df = pd.read_csv(file_path)

    date_col = _detect_date_column(df)
    value_col = _detect_value_column(df, exclude=date_col)

    logger.info("Detected columns — date: %s, value: %s", date_col, value_col)

    series = _dataframe_to_series(df, date_col=date_col, value_col=value_col)

    metadata = {
        "detected_date_col": date_col,
        "detected_value_col": value_col,
        "period_count": len(series),
        "frequency": "W",
        "preview": df[[date_col, value_col]].head(5).to_dict(orient="records"),
    }
    return series, metadata


def _detect_date_column(df: pd.DataFrame) -> str:
    """
    Identify the date column by name heuristic then by parseability.

    We prioritize name-based matching because it is faster and more reliable
    than trying to parse every column as a date.

    Args:
        df: Raw DataFrame from pd.read_csv.

    Returns:
        Column name of the detected date column.

    Raises:
        ValueError: If no column can be parsed as dates.
    """
    lower_cols = {col.lower(): col for col in df.columns}

    # Name-based detection (fastest path)
    for hint in DATE_COLUMN_HINTS:
        if hint in lower_cols:
            candidate = lower_cols[hint]
            try:
                pd.to_datetime(df[candidate])
                return candidate
            except Exception:
                pass

    # Fallback: try to parse each column as dates
    for col in df.columns:
        try:
            parsed = pd.to_datetime(df[col])
            if parsed.notna().sum() > len(df) * 0.8:  # 80%+ parseable
                return col
        except Exception:
            continue

    raise ValueError(
        "Could not identify a date column. "
        "Please ensure your CSV has a column named 'date', 'week', 'period', or similar."
    )


def _detect_value_column(df: pd.DataFrame, exclude: str) -> str:
    """
    Identify the numeric value column, excluding the date column.

    Args:
        df: Raw DataFrame.
        exclude: Column name to skip (the date column).

    Returns:
        Column name of the detected value column.

    Raises:
        ValueError: If no numeric column is found.
    """
    lower_cols = {col.lower(): col for col in df.columns if col != exclude}

    # Name-based detection
    for hint in VALUE_COLUMN_HINTS:
        if hint in lower_cols:
            candidate = lower_cols[hint]
            if pd.api.types.is_numeric_dtype(df[candidate]):
                return candidate

    # Fallback: first numeric column that is not the date column
    for col in df.columns:
        if col != exclude and pd.api.types.is_numeric_dtype(df[col]):
            return col

    raise ValueError(
        "Could not identify a numeric value column. "
        "Please ensure your CSV has a column named 'value', 'amount', 'volume', or similar."
    )


def _dataframe_to_series(
    df: pd.DataFrame,
    source_label: str = "uploaded",
    date_col: Optional[str] = None,
    value_col: Optional[str] = None,
) -> pd.Series:
    """
    Convert a two-column DataFrame to a validated, resampled weekly pd.Series.

    Steps:
    1. Parse and set the DatetimeIndex.
    2. Extract the value column.
    3. Interpolate missing values linearly.
    4. Resample to weekly frequency (mean aggregation for sub-weekly data).
    5. Validate minimum length.

    Args:
        df: Input DataFrame.
        source_label: Human-readable label for error messages.
        date_col: Name of the date column (auto-detected if None).
        value_col: Name of the value column (auto-detected if None).

    Returns:
        Weekly pd.Series with float64 dtype.

    Raises:
        ValueError: If the processed series has fewer than MIN_PERIODS points.
    """
    if date_col is None:
        date_col = _detect_date_column(df)
    if value_col is None:
        value_col = _detect_value_column(df, exclude=date_col)

    df = df[[date_col, value_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col).set_index(date_col)
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

    series = df[value_col].rename("value")

    # Linear interpolation fills isolated NaN gaps without distorting trends
    series = series.interpolate(method="linear", limit_direction="both")

    # Resample to weekly (Monday-anchored) — no-op if already weekly
    series = series.resample("W-MON").mean()

    if len(series) < MIN_PERIODS:
        raise ValueError(
            f"Dataset '{source_label}' has only {len(series)} weekly periods "
            f"after resampling. Minimum required: {MIN_PERIODS}."
        )

    logger.info(
        "Parsed '%s': %d weekly periods from %s to %s",
        source_label,
        len(series),
        series.index[0].date(),
        series.index[-1].date(),
    )
    return series
