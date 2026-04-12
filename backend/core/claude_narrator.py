"""
Claude API integration for plain-English briefings and anomaly explanations.

All Claude calls are made from the backend. The API key is never sent to
the frontend. Streaming is implemented via Server-Sent Events (SSE) so
users see the response token-by-token.
"""

import json
import logging
import os
from typing import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 400  # Keeps briefings concise (roughly 3–5 sentences)


def _get_api_key() -> str:
    """
    Retrieve the Anthropic API key from environment variables.

    Raises:
        EnvironmentError: If ANTHROPIC_API_KEY is not set, so the error
            surfaces immediately at runtime rather than failing silently.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file."
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
    """
    Construct the prompt sent to Claude for the plain-English briefing.

    The prompt is structured to produce concise, actionable language
    suitable for non-technical banking managers (no jargon, no formulas).

    Args:
        metric: Friendly metric name (e.g. 'Transaction Volume').
        trend: Detected trend direction ('upward', 'downward', 'flat').
        horizon_weeks: Forecast horizon in weeks.
        anomaly_count: Number of anomalies detected in historical data.
        forecast_summary: Pre-built summary of forecast figures.
        model_used: Model name used for the forecast ('Prophet' or 'AutoETS').

    Returns:
        Complete prompt string for Claude.
    """
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
    """
    Build a prompt for Claude to generate a one-sentence anomaly explanation.

    Args:
        metric: Metric name.
        date: Date of the anomaly.
        value: Observed value.
        zscore: Z-score deviation.
        severity: 'warning' or 'critical'.
        expected_range: [lower_bound, upper_bound] of normal range.

    Returns:
        Prompt string for Claude.
    """
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
    Stream a Claude-generated briefing as Server-Sent Events tokens.

    Each yielded string is an SSE-formatted message ready for the response.
    The final event has {"done": true} to signal stream completion.

    Args:
        metric: Metric name for the briefing context.
        trend: Trend direction.
        horizon_weeks: Forecast horizon.
        anomaly_count: Number of detected anomalies.
        forecast_summary: Pre-built forecast summary string.
        model_used: Model name used.

    Yields:
        SSE-formatted string events: 'data: {"token": "..."}\n\n'
        Final event: 'data: {"done": true}\n\n'
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
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": MAX_TOKENS,
        "stream": True,
        "messages": [{"role": "user", "content": prompt}],
    }

    logger.info("Initiating Claude streaming briefing for metric: %s", metric)

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", CLAUDE_API_URL, headers=headers, json=payload) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                logger.error("Claude API error %d: %s", response.status_code, error_body)
                yield f'data: {json.dumps({"error": "Claude API error"})}\n\n'
                return

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue

                raw = line[6:]  # Strip 'data: ' prefix
                if raw == "[DONE]":
                    break

                try:
                    event = json.loads(raw)
                    if event.get("type") == "content_block_delta":
                        token = event.get("delta", {}).get("text", "")
                        if token:
                            yield f'data: {json.dumps({"token": token})}\n\n'
                except json.JSONDecodeError:
                    continue

    yield f'data: {json.dumps({"done": True})}\n\n'
    logger.info("Claude briefing stream complete")


async def generate_anomaly_explanation(
    metric: str,
    date: str,
    value: float,
    zscore: float,
    severity: str,
    expected_range: list,
) -> str:
    """
    Call Claude synchronously (non-streaming) to generate a one-sentence anomaly explanation.

    This is called once per anomaly during the /forecast endpoint response build,
    not during the streaming SSE endpoint. Explanations are cached in the response
    so the UI does not need to make separate calls per anomaly.

    Args:
        metric: Metric name.
        date: Anomaly date string.
        value: Observed value.
        zscore: Z-score.
        severity: 'warning' or 'critical'.
        expected_range: [lower, upper] expected range.

    Returns:
        One-sentence explanation string, or a fallback if the API call fails.
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
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 120,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CLAUDE_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"].strip()
    except Exception as exc:
        logger.warning("Anomaly explanation generation failed: %s", exc)
        return (
            f"Value of {value:,.2f} on {date} was {abs(zscore):.1f}σ from the mean. "
            f"Suggested action: Investigate with your operations team."
        )
