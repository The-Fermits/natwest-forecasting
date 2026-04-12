'use client';

import React, { useState } from 'react';
import type { ModelAccuracy, Patterns, TrainingRange } from '@/lib/types';
import { formatPercent, formatDate, trendLabel } from '@/lib/utils';

interface Props {
    modelUsed: string;
    trainingRange: TrainingRange;
    confidenceLevel: number;
    accuracy: ModelAccuracy;
    patterns: Patterns;
}

export default function TransparencyPanel({
    modelUsed,
    trainingRange,
    confidenceLevel,
    accuracy,
    patterns,
}: Props) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between group"
            >
                <div className="flex items-center gap-3">
                    <span className="text-xl">🔬</span>
                    <div className="text-left">
                        <h3 className="font-bold text-gray-900">How This Was Computed</h3>
                        <p className="text-xs text-gray-500 mt-0.5">Model details, accuracy, and detected patterns</p>
                    </div>
                </div>
                <span className="text-gray-400 group-hover:text-gray-600 transition-colors text-lg">
                    {expanded ? '▾' : '▸'}
                </span>
            </button>

            {expanded && (
                <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Model info */}
                    <div className="bg-gray-50 rounded-xl p-4 space-y-2">
                        <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-3">Model</h4>
                        <Row label="Algorithm" value={modelUsed} highlight />
                        <Row label="Training start" value={formatDate(trainingRange.start)} />
                        <Row label="Training end" value={formatDate(trainingRange.end)} />
                        <Row label="Period count" value={`${trainingRange.period_count} weeks`} />
                        <Row label="Confidence interval" value={`${(confidenceLevel * 100).toFixed(0)}%`} />
                    </div>

                    {/* Accuracy */}
                    <div className="bg-gray-50 rounded-xl p-4 space-y-2">
                        <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-3">Validation Accuracy</h4>
                        <Row label={`${modelUsed} MAPE`} value={accuracy.mape !== null ? formatPercent(accuracy.mape) : 'Insufficient data'} highlight />
                        <Row label={`${modelUsed} RMSE`} value={accuracy.rmse !== null ? `${accuracy.rmse.toFixed(0)}` : '—'} />
                        <Row label="Naive baseline MAPE" value={formatPercent(accuracy.baseline_naive_mape)} />
                        <Row label="MA(4) baseline MAPE" value={formatPercent(accuracy.baseline_ma_mape)} />
                        <Row
                            label="AI vs baseline"
                            value={
                                accuracy.outperformance_pct > 0
                                    ? `+${accuracy.outperformance_pct.toFixed(1)}% better`
                                    : `${Math.abs(accuracy.outperformance_pct).toFixed(1)}% worse`
                            }
                            highlight
                        />
                    </div>

                    {/* Patterns */}
                    <div className="bg-gray-50 rounded-xl p-4 space-y-2 md:col-span-2">
                        <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-3">Detected Patterns</h4>
                        <Row label="Trend direction" value={trendLabel(patterns.trend)} highlight />
                        <Row
                            label="Seasonality period"
                            value={patterns.seasonality_period ? `${patterns.seasonality_period} weeks (annual)` : 'None detected'}
                        />
                        <Row
                            label="Seasonality strength (ACF)"
                            value={patterns.seasonality_strength !== null ? patterns.seasonality_strength.toFixed(3) : '—'}
                        />
                        <Row
                            label="Model selection rationale"
                            value={
                                modelUsed === 'Prophet'
                                    ? 'Prophet selected: ≥52 weeks data + strong annual autocorrelation (ACF > 0.4)'
                                    : 'AutoETS selected: short series or weak seasonality (ACF ≤ 0.4)'
                            }
                        />
                    </div>
                </div>
            )}
        </div>
    );
}

function Row({ label, value, highlight = false }: { label: string; value: string | number; highlight?: boolean }) {
    return (
        <div className="flex items-start justify-between gap-3">
            <span className="text-xs text-gray-500 flex-1">{label}</span>
            <span className={`text-xs font-semibold text-right ${highlight ? 'text-purple-700' : 'text-gray-800'}`}>
                {value}
            </span>
        </div>
    );
}
