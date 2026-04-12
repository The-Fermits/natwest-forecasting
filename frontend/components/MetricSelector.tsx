'use client';

import React from 'react';
import { METRIC_LABELS, MetricKey } from '@/lib/types';

interface Props {
    value: MetricKey;
    onChange: (metric: MetricKey) => void;
}

const METRICS = Object.entries(METRIC_LABELS) as [MetricKey, string][];

export default function MetricSelector({ value, onChange }: Props) {
    return (
        <select
            id="metric-select"
            value={value}
            onChange={(e) => onChange(e.target.value as MetricKey)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 text-gray-700 font-medium bg-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
        >
            {METRICS.map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
            ))}
        </select>
    );
}
