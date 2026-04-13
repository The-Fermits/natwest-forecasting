"""
SSE streaming endpoint for Gemini AI plain-English briefings.

The endpoint streams Gemini's response token-by-token to the frontend
so users see text appearing in real time, creating a more responsive
experience than waiting for the full response.
"""

import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from core.gemini_narrator import stream_briefing

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/briefing")
async def get_briefing(
    metric: str = "transaction_volume",
    trend: str = "flat",
    horizon: int = 4,
    anomaly_count: int = 0,
    forecast_summary: str = "No summary available.",
    model_used: str = "AutoETS",
) -> StreamingResponse:
    """
    Stream a Gemini-generated plain-English briefing via Server-Sent Events.

    Query parameters are used (rather than POST body) so the frontend can
    initiate the SSE connection with a standard EventSource — the Web API
    for SSE only supports GET requests.

    Args:
        metric: Metric identifier for context.
        trend: Detected trend direction.
        horizon: Forecast horizon in weeks.
        anomaly_count: Number of anomalies detected.
        forecast_summary: Pre-computed text summary of forecast values.
        model_used: Model name for transparency.

    Returns:
        StreamingResponse with text/event-stream content type.
    """
    async def event_generator():
        async for chunk in stream_briefing(
            metric=metric,
            trend=trend,
            horizon_weeks=horizon,
            anomaly_count=anomaly_count,
            forecast_summary=forecast_summary,
            model_used=model_used,
        ):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for SSE
        },
    )
