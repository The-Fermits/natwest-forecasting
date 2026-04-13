// Utility functions for formatting and display

/**
 * Format a number as a human-readable string with commas and optional decimal places.
 */
export function formatNumber(value: number, decimals = 0): string {
    if (value === null || value === undefined || isNaN(value)) return '—';
    return new Intl.NumberFormat('en-GB', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(value);
}

/**
 * Format a percentage value for display (e.g. 4.2 → "4.2%").
 */
export function formatPercent(value: number | null, decimals = 1): string {
    if (value === null || value === undefined || isNaN(value)) return '—';
    return `${value.toFixed(decimals)}%`;
}

/**
 * Format a date string to locale-friendly format (e.g. "7 Jan 2024").
 */
export function formatDate(dateString: string): string {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

/**
 * Compute the percentage change between two values.
 * Returns formatted string like "+5.2%" or "–3.1%".
 */
export function pctChange(from: number, to: number, decimals = 1): string {
    if (from === 0) return '—';
    const change = ((to - from) / Math.abs(from)) * 100;
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(decimals)}%`;
}

/**
 * Map a trend direction string to a user-friendly emoji + label.
 */
export function trendLabel(trend: string): string {
    if (trend === 'upward') return '↑ Upward';
    if (trend === 'downward') return '↓ Downward';
    return '→ Flat';
}

/**
 * Return a Tailwind color class for a data quality status.
 */
export function qualityStatusColor(status: 'pass' | 'warn' | 'fail'): string {
    if (status === 'pass') return 'text-emerald-600';
    if (status === 'warn') return 'text-amber-600';
    return 'text-red-600';
}

/**
 * Return a Tailwind badge class for an anomaly severity.
 */
export function severityBadgeClass(severity: 'warning' | 'critical'): string {
    if (severity === 'critical') return 'bg-red-100 text-red-700 border-red-200';
    return 'bg-amber-100 text-amber-700 border-amber-200';
}

/**
 * Build a plain-text forecast summary for use in the Gemini briefing prompt.
 */
export function buildForecastSummary(
    forecast: Array<{ date: string; lower: number; central: number; upper: number }>,
    historicalLast: number,
): string {
    if (!forecast.length) return 'No forecast data.';
    const first = forecast[0];
    const last = forecast[forecast.length - 1];
    const change = pctChange(historicalLast, last.central);
    return (
        `Over the next ${forecast.length} week(s): central estimate goes from ` +
        `${formatNumber(first.central)} to ${formatNumber(last.central)} (${change}). ` +
        `Final week range: ${formatNumber(last.lower)}–${formatNumber(last.upper)}.`
    );
}

/**
 * Clamp a number between min and max.
 */
export function clamp(value: number, min: number, max: number): number {
    return Math.min(Math.max(value, min), max);
}
