"""
Google Gemini API integration for plain-English briefings and anomaly explanations.

All Gemini calls are made from the backend. The API key is never sent to
the frontend. Streaming is implemented via Server-Sent Events (SSE) so
users see the response token-by-token.
"""

import json
import logging
import os
from typing import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"


def _get_api_key() -> str:
    """
    Retrieve the Gemini API key from environment variables.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )
    return api_key


def build_briefing_prompt(
    metric: str,
    trend: str,
    horizon_weeks: int,
    anomaly_count: int,
    forecast_summary: str,
    model_used: str,
) -> str:
    anomaly_clause = (
        f"{anomaly_count} unusual data point(s) were detected in the historical series."
        if anomaly_count > 0
        else "No anomalies were detected in the historical data."
    )

    return f"""You are a senior banking analytics AI assistant. Write a concise, plain-English briefing 
for a non-technical bank branch manager or risk officer.

DATA CONTEXT:
- Metric: {metric}
- Trend direction: {trend}
- Forecast horizon: {horizon_weeks} weeks ahead
- Model used: {model_used}
- Forecast summary: {forecast_summary}
- Anomaly status: {anomaly_clause}

BRIEFING REQUIREMENTS:
1. Write exactly 3–5 sentences. No bullet points, no headers.
2. Cover: overall trend direction, key uncertainty, any anomalies, and one specific actionable recommendation.
3. Use simple English suitable for a non-technical banking manager. No statistical jargon.
4. Be direct and specific — reference week numbers and % figures where relevant.
5. Tone: professional, calm, and informative. Not alarmist.

Write the briefing now:"""


def build_anomaly_explanation_prompt(
    metric: str,
    date: str,
    value: float,
    zscore: float,
    severity: str,
    expected_range: list,
) -> str:
    return f"""In one sentence, explain why the following banking data anomaly may have occurred and suggest one next step.

Metric: {metric}
Date: {date}
Observed value: {value:,.2f}
Expected range: {expected_range[0]:,.2f} to {expected_range[1]:,.2f}
Z-score deviation: {abs(zscore):.1f}σ ({severity})

Response format: "[Brief potential cause]. Suggested action: [specific next step]."
Do not start with "I" or use jargon. Write for a non-technical bank manager."""


async def stream_briefing(
    metric: str,
    trend: str,
    horizon_weeks: int,
    anomaly_count: int,
    forecast_summary: str,
    model_used: str,
) -> AsyncGenerator[str, None]:
    """
    Stream a Gemini-generated briefing as Server-Sent Events tokens.
    """
    prompt = build_briefing_prompt(
        metric=metric,
        trend=trend,
        horizon_weeks=horizon_weeks,
        anomaly_count=anomaly_count,
        forecast_summary=forecast_summary,
        model_used=model_used,
    )

    api_key = _get_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    logger.info("Initiating Gemini streaming briefing for metric: %s", metric)

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                logger.error("Gemini API error %d: %s", response.status_code, error_body)
                yield f'data: {json.dumps({"error": "Gemini API error"})}\n\n'
                return

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue

                raw = line[6:]
                if not raw:
                    continue
                    
                try:
                    event = json.loads(raw)
                    if "candidates" in event:
                        candidate = event["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            token = candidate["content"]["parts"][0].get("text", "")
                            if token:
                                yield f'data: {json.dumps({"token": token})}\n\n'
                except Exception:
                    continue

    yield f'data: {json.dumps({"done": True})}\n\n'
    logger.info("Gemini briefing stream complete")


async def generate_anomaly_explanation(
    metric: str,
    date: str,
    value: float,
    zscore: float,
    severity: str,
    expected_range: list,
) -> str:
    """
    Call Gemini synchronously (non-streaming) to generate a one-sentence anomaly explanation.
    """
    prompt = build_anomaly_explanation_prompt(
        metric=metric,
        date=date,
        value=value,
        zscore=zscore,
        severity=severity,
        expected_range=expected_range,
    )

    api_key = _get_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as exc:
        logger.warning("Anomaly explanation generation failed: %s", exc)
        return (
            f"Value of {value:,.2f} on {date} was {abs(zscore):.1f}σ from the mean. "
            f"Suggested action: Investigate with your operations team."
        )
