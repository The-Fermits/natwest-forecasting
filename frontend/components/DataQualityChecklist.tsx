'use client';

import React from 'react';
import type { DataQualityCheck } from '@/lib/types';

interface Props {
    checks: DataQualityCheck[];
}

const CHECK_LABELS: Record<string, string> = {
    missing_values: 'Missing Values',
    data_length: 'Data Length',
    irregular_intervals: 'Time Intervals',
    extreme_outliers: 'Extreme Outliers',
};

const STATUS_CONFIG = {
    pass: { icon: '✓', bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700', badge: 'PASS' },
    warn: { icon: '⚠', bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', badge: 'WARN' },
    fail: { icon: '✕', bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', badge: 'FAIL' },
};

export default function DataQualityChecklist({ checks }: Props) {
    const hasWarning = checks.some((c) => c.status === 'warn');
    const hasFail = checks.some((c) => c.status === 'fail');

    if (checks.every((c) => c.status === 'pass')) {
        return (
            <div className="bg-emerald-50 border border-emerald-200 rounded-2xl px-5 py-3 flex items-center gap-3">
                <span className="text-emerald-500 text-lg">✓</span>
                <span className="text-emerald-700 text-sm font-medium">All pre-flight checks passed</span>
            </div>
        );
    }

    return (
        <div className={`rounded-2xl border p-5 ${hasFail ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200'}`}>
            <div className="flex items-center gap-2 mb-4">
                <span className="text-lg">{hasFail ? '🔴' : '🟡'}</span>
                <h3 className="font-bold text-gray-900 text-sm">
                    Data Quality Pre-flight{hasFail ? ' — Blocked' : ' — Warnings'}
                </h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {checks.map((check) => {
                    const config = STATUS_CONFIG[check.status];
                    return (
                        <div key={check.check} className={`rounded-xl border ${config.bg} ${config.border} p-3`}>
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-xs font-semibold text-gray-700">
                                    {CHECK_LABELS[check.check] || check.check}
                                </span>
                                <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${config.text} bg-white border ${config.border}`}>
                                    {config.badge}
                                </span>
                            </div>
                            <p className="text-xs text-gray-500 leading-snug">{check.detail}</p>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
