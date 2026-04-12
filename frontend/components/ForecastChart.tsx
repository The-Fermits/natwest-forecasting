'use client';

import React, { useMemo } from 'react';
import {
    ComposedChart,
    Area,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ReferenceLine,
    ReferenceDot,
    ResponsiveContainer,
    Legend,
} from 'recharts';
import type { HistoricalPoint, ForecastPoint, BaselinePoint, AnomalyPoint } from '@/lib/types';
import { formatNumber, formatDate } from '@/lib/utils';

interface Props {
    historical: HistoricalPoint[];
    forecast: ForecastPoint[];
    baselineNaive: BaselinePoint[];
    baselineMA: BaselinePoint[];
    anomalies: AnomalyPoint[];
    confidenceLevel: number;
}

// Merge all data into a single chart-friendly array
// Historical points have 'historical' field; forecast points have lower/central/upper
type ChartRow = {
    date: string;
    historical?: number;
    central?: number;
    lower?: number;
    upper?: number;
    naive?: number;
    ma?: number;
    isForecast: boolean;
};

export default function ForecastChart({
    historical,
    forecast,
    baselineNaive,
    baselineMA,
    anomalies,
    confidenceLevel,
}: Props) {
    const chartData = useMemo<ChartRow[]>(() => {
        const naiveByDate: Record<string, number> = {};
        baselineNaive.forEach((b) => { naiveByDate[b.date] = b.value; });
        const maByDate: Record<string, number> = {};
        baselineMA.forEach((b) => { maByDate[b.date] = b.value; });

        const historicalRows: ChartRow[] = historical.map((h) => ({
            date: h.date,
            historical: h.value,
            isForecast: false,
        }));

        const forecastRows: ChartRow[] = forecast.map((f) => ({
            date: f.date,
            central: f.central,
            lower: f.lower,
            upper: f.upper,
            naive: naiveByDate[f.date],
            ma: maByDate[f.date],
            isForecast: true,
        }));

        return [...historicalRows, ...forecastRows];
    }, [historical, forecast, baselineNaive, baselineMA]);

    const anomalyByDate = useMemo(() => {
        const map: Record<string, AnomalyPoint> = {};
        anomalies.forEach((a) => { map[a.date] = a; });
        return map;
    }, [anomalies]);

    const splitDate = historical.length > 0 ? historical[historical.length - 1].date : '';

    // Determine sensible Y-axis domain
    const allValues = [
        ...historical.map((h) => h.value),
        ...forecast.flatMap((f) => [f.lower, f.upper]),
    ].filter(Boolean);
    const minVal = Math.min(...allValues) * 0.9;
    const maxVal = Math.max(...allValues) * 1.1;

    const labelInterval = Math.max(1, Math.floor(chartData.length / 8));

    return (
        <ResponsiveContainer width="100%" height={360}>
            <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />

                <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickLine={false}
                    axisLine={false}
                    interval={labelInterval}
                    tickFormatter={(d) => {
                        const dt = new Date(d);
                        return dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
                    }}
                />

                <YAxis
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickLine={false}
                    axisLine={false}
                    domain={[minVal, maxVal]}
                    tickFormatter={(v) => formatNumber(v)}
                    width={80}
                />

                <Tooltip
                    content={({ active, payload, label }) => {
                        if (!active || !payload?.length) return null;
                        const anomaly = anomalyByDate[label as string];
                        return (
                            <div className="bg-white border border-gray-200 rounded-xl shadow-lg p-3 text-sm min-w-[180px]">
                                <p className="font-semibold text-gray-700 mb-2">{formatDate(label as string)}</p>
                                {payload.map((p) => (
                                    p.value !== undefined && p.value !== null && (
                                        <div key={p.name} className="flex justify-between gap-4 text-xs">
                                            <span style={{ color: p.color }}>{p.name}</span>
                                            <span className="font-medium text-gray-800">{formatNumber(p.value as number, 2)}</span>
                                        </div>
                                    )
                                ))}
                                {anomaly && (
                                    <div className={`mt-2 pt-2 border-t border-gray-100 text-xs font-medium ${anomaly.severity === 'critical' ? 'text-red-600' : 'text-amber-600'}`}>
                                        ⚠ {anomaly.severity === 'critical' ? 'Critical' : 'Warning'} anomaly ({anomaly.zscore > 0 ? '+' : ''}{anomaly.zscore.toFixed(1)}σ)
                                    </div>
                                )}
                            </div>
                        );
                    }}
                />

                {/* Confidence band for forecast */}
                <Area
                    dataKey="upper"
                    stroke="none"
                    fill="#7C3AED"
                    fillOpacity={0.12}
                    name={`${confidenceLevel === 0.95 ? '95%' : '80%'} upper`}
                    legendType="none"
                    connectNulls
                />
                <Area
                    dataKey="lower"
                    stroke="none"
                    fill="#ffffff"
                    fillOpacity={1}
                    name={`${confidenceLevel === 0.95 ? '95%' : '80%'} lower`}
                    legendType="none"
                    connectNulls
                />

                {/* Historical data line */}
                <Line
                    dataKey="historical"
                    stroke="#6B7280"
                    strokeWidth={2}
                    dot={false}
                    name="Historical"
                    connectNulls
                />

                {/* AI forecast central line */}
                <Line
                    dataKey="central"
                    stroke="#5B21B6"
                    strokeWidth={2.5}
                    dot={false}
                    name="AI Forecast"
                    connectNulls
                />

                {/* Naive baseline (dashed amber) */}
                <Line
                    dataKey="naive"
                    stroke="#F59E0B"
                    strokeWidth={1.5}
                    strokeDasharray="5 3"
                    dot={false}
                    name="Naive Baseline"
                    connectNulls
                />

                {/* MA baseline (dashed teal) */}
                <Line
                    dataKey="ma"
                    stroke="#10B981"
                    strokeWidth={1.5}
                    strokeDasharray="5 3"
                    dot={false}
                    name="MA(4) Baseline"
                    connectNulls
                />

                {/* Vertical separator: historical vs forecast */}
                {splitDate && (
                    <ReferenceLine
                        x={splitDate}
                        stroke="#d1d5db"
                        strokeDasharray="4 3"
                        strokeWidth={1.5}
                        label={{ value: 'Forecast →', position: 'top', fontSize: 10, fill: '#9ca3af' }}
                    />
                )}

                {/* Anomaly dots */}
                {anomalies.map((a) => (
                    <ReferenceDot
                        key={a.date}
                        x={a.date}
                        y={a.value}
                        r={5}
                        fill={a.severity === 'critical' ? '#EF4444' : '#F59E0B'}
                        stroke="white"
                        strokeWidth={1.5}
                        label=""
                    />
                ))}

                <Legend
                    wrapperStyle={{ fontSize: '11px', paddingTop: '12px' }}
                    iconType="line"
                    iconSize={20}
                />
            </ComposedChart>
        </ResponsiveContainer>
    );
}
