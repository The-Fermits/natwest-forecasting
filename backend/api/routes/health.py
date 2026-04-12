"""
FastAPI health check endpoint.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """
    Return service health status.

    Used by UptimeRobot (or similar) to prevent Render free-tier sleep.
    Also confirms that the Python environment and imports are functional.
    """
    return {"status": "ok", "model_ready": True}
