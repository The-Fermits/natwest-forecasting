'use client';

import React, { useState } from 'react';
import type { AnomalyPoint } from '@/lib/types';
import { formatNumber, formatDate, severityBadgeClass } from '@/lib/utils';

interface Props {
    anomalies: AnomalyPoint[];
    metricLabel: string;
}

export default function AnomalyPanel({ anomalies, metricLabel }: Props) {
    const [expanded, setExpanded] = useState(true);

    const criticalCount = anomalies.filter((a) => a.severity === 'critical').length;
    const warningCount = anomalies.filter((a) => a.severity === 'warning').length;

    return (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between group"
            >
                <div className="flex items-center gap-3">
                    <span className="text-xl">🔍</span>
                    <div className="text-left">
                        <h3 className="font-bold text-gray-900">Anomaly Alert Panel</h3>
                        <p className="text-xs text-gray-500 mt-0.5">
                            {criticalCount > 0 && <span className="text-red-600 font-medium">{criticalCount} critical</span>}
                            {criticalCount > 0 && warningCount > 0 && ', '}
                            {warningCount > 0 && <span className="text-amber-600 font-medium">{warningCount} warning</span>}
                            {criticalCount === 0 && warningCount === 0 && 'No anomalies detected'}
                        </p>
                    </div>
                </div>
                <span className="text-gray-400 group-hover:text-gray-600 transition-colors text-lg">
                    {expanded ? '▾' : '▸'}
                </span>
            </button>

            {expanded && (
                <div className="mt-4 space-y-3">
                    {anomalies.map((anomaly) => (
                        <div
                            key={anomaly.date}
                            className={`rounded-xl border p-4 ${anomaly.severity === 'critical'
                                    ? 'bg-red-50 border-red-200'
                                    : 'bg-amber-50 border-amber-200'
                                }`}
                        >
                            <div className="flex items-start justify-between gap-3">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${severityBadgeClass(anomaly.severity)}`}>
                                            {anomaly.severity === 'critical' ? '🔴 Critical' : '🟡 Warning'}
                                        </span>
                                        <span className="text-xs text-gray-500">{formatDate(anomaly.date)}</span>
                                    </div>
                                    <p className="text-sm font-semibold text-gray-800">
                                        {metricLabel}: <span className="text-gray-900">{formatNumber(anomaly.value, 2)}</span>
                                        <span className="text-gray-500 font-normal ml-1">
                                            ({anomaly.zscore > 0 ? '+' : ''}{anomaly.zscore.toFixed(1)}σ from mean)
                                        </span>
                                    </p>
                                    <p className="text-xs text-gray-500 mt-0.5">
                                        Expected range: {formatNumber(anomaly.expected_range[0], 0)} – {formatNumber(anomaly.expected_range[1], 0)}
                                    </p>
                                    {anomaly.explanation && (
                                        <p className="text-xs text-gray-600 mt-2 italic leading-relaxed">
                                            {anomaly.explanation}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}

                    {anomalies.length === 0 && (
                        <div className="text-center py-6 text-gray-400 text-sm">
                            <span className="text-2xl block mb-2">✓</span>
                            No anomalies detected in the historical data.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
