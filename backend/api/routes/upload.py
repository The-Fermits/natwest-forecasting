"""
CSV upload endpoint — accepts user-provided time-series files for forecasting.

Files are written to a session-specific temporary path, processed, and the
session ID is returned for subsequent /forecast calls. Files are never persisted
beyond the session lifetime (UPLOAD_TTL_SECONDS from env config).
"""

import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from core.ingestion import load_uploaded_csv, MIN_PERIODS

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOADS_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)) -> JSONResponse:
    """
    Accept a CSV file upload, validate it, and return a session ID for forecasting.

    The endpoint reads the file fully into memory, writes it to a temp path,
    then uses the ingestion module to auto-detect columns and validate length.

    Args:
        file: Uploaded CSV file from multipart/form-data.

    Returns:
        JSON with session_id, preview rows, detected column names, period count,
        and frequency string.

    Raises:
        HTTPException 400: File too large, not a CSV, or failing validation.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_UPLOAD_BYTES // (1024*1024)} MB.",
        )

    session_id = str(uuid.uuid4())
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    upload_path = UPLOADS_DIR / f"{session_id}.csv"

    upload_path.write_bytes(content)
    logger.info("Saved upload: %s (%d bytes)", session_id, len(content))

    try:
        _, metadata = load_uploaded_csv(upload_path)
    except ValueError as exc:
        upload_path.unlink(missing_ok=True)  # Clean up invalid file immediately
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        upload_path.unlink(missing_ok=True)
        logger.error("Upload parsing failed for session %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail="Failed to parse uploaded CSV.") from exc

    return JSONResponse({
        "session_id": session_id,
        **metadata,
    })
