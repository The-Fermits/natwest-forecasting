// API client: all fetch calls to the backend
// Backend URL is configured via NEXT_PUBLIC_API_URL environment variable.

import type {
    ForecastResponse,
    ForecastPoint,
    MetricKey,
    ScenarioResponse,
    UploadResponse,
    ConfidenceLevel,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Run the full forecasting pipeline for a default dataset metric.
 */
export async function fetchForecast(
    metric: MetricKey,
    horizonWeeks: number,
    confidenceLevel: ConfidenceLevel,
    sessionId?: string,
): Promise<ForecastResponse> {
    const response = await fetch(`${API_BASE}/forecast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            metric,
            session_id: sessionId ?? null,
            horizon_weeks: horizonWeeks,
            confidence_level: confidenceLevel,
        }),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(
            typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail),
        );
    }
    return response.json();
}

/**
 * Upload a CSV file and return the session ID and metadata.
 */
export async function uploadCSV(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Upload failed');
    }
    return response.json();
}

/**
 * Apply scenario adjustments to a base forecast.
 */
export async function fetchScenario(
    baseForecast: ForecastPoint[],
    growthRate: number,
    removeOutliers: boolean,
    seasonalBoost?: { week: number; pct: number },
): Promise<ScenarioResponse> {
    const response = await fetch(`${API_BASE}/scenario`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            base_forecast: baseForecast,
            growth_rate: growthRate,
            remove_outliers: removeOutliers,
            seasonal_boost: seasonalBoost ?? null,
        }),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Scenario failed');
    }
    return response.json();
}

/**
 * Build the SSE briefing URL for use with EventSource.
 * Returns a URL string because EventSource only accepts GET URLs.
 */
export function buildBriefingUrl(params: {
    metric: string;
    trend: string;
    horizon: number;
    anomalyCount: number;
    forecastSummary: string;
    modelUsed: string;
}): string {
    const qs = new URLSearchParams({
        metric: params.metric,
        trend: params.trend,
        horizon: String(params.horizon),
        anomaly_count: String(params.anomalyCount),
        forecast_summary: params.forecastSummary,
        model_used: params.modelUsed,
    });
    return `${API_BASE}/briefing?${qs.toString()}`;
}

/**
 * Check backend health.
 */
export async function checkHealth(): Promise<{ status: string; model_ready: boolean }> {
    const response = await fetch(`${API_BASE}/health`);
    return response.json();
}
