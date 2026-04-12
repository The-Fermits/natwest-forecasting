"""
Anomaly detection endpoint — runs only anomaly detection on a given dataset.

This is a lightweight endpoint for the anomaly panel refresh without
re-running the full forecast pipeline.
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.ingestion import load_default_series, load_uploaded_csv
from core.anomaly_detector import detect_anomalies

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOADS_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"


class AnomalyRequest(BaseModel):
    metric: str
    session_id: Optional[str] = None


@router.post("/anomaly")
async def run_anomaly_detection(request: AnomalyRequest) -> dict:
    """
    Run Z-score and IQR anomaly detection on the specified dataset.

    Args:
        request: AnomalyRequest with metric key or session_id.

    Returns:
        Dict with anomalies list.

    Raises:
        HTTPException 400: Dataset not found.
    """
    try:
        if request.session_id:
            upload_path = UPLOADS_DIR / f"{request.session_id}.csv"
            if not upload_path.exists():
                raise HTTPException(status_code=400, detail="Upload session not found.")
            series, _ = load_uploaded_csv(upload_path)
        else:
            series = load_default_series(request.metric)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    anomalies = detect_anomalies(series)
    return {"anomalies": anomalies, "total": len(anomalies)}
