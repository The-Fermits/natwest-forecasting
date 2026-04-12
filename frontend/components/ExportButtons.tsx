'use client';

import React from 'react';
import type { ForecastResponse } from '@/lib/types';

interface Props {
    forecastData: ForecastResponse;
    metricLabel: string;
}

export default function ExportButtons({ forecastData, metricLabel }: Props) {
    const handleExportCSV = () => {
        const rows = [
            ['date', 'lower', 'central', 'upper', 'historical', 'naive_baseline', 'ma_baseline', 'anomaly_flag'],
            ...forecastData.forecast.map((f, i) => [
                f.date,
                f.lower,
                f.central,
                f.upper,
                '',
                forecastData.baseline_naive[i]?.value ?? '',
                forecastData.baseline_ma[i]?.value ?? '',
                '',
            ]),
        ];

        const csvContent = rows.map((r) => r.join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `natwest_forecast_${metricLabel.toLowerCase().replace(/\s+/g, '_')}.csv`;
        link.click();
        URL.revokeObjectURL(url);
    };

    const handleExportPNG = () => {
        // Use html2canvas-like approach: find the chart container and print it
        const chartEl = document.getElementById('forecast-chart-container');
        if (!chartEl) {
            alert('Chart element not found.');
            return;
        }

        import('html2canvas').then((mod) => {
            const html2canvas = mod.default;
            html2canvas(chartEl, { scale: 2, backgroundColor: '#ffffff' }).then((canvas) => {
                const url = canvas.toDataURL('image/png');
                const link = document.createElement('a');
                link.href = url;
                link.download = `natwest_forecast_${metricLabel.toLowerCase().replace(/\s+/g, '_')}.png`;
                link.click();
            });
        });
    };

    return (
        <div className="flex items-center gap-2">
            <button
                id="export-csv-btn"
                onClick={handleExportCSV}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-gray-600 bg-white border border-gray-300 rounded-lg hover:border-purple-400 hover:text-purple-700 transition-colors"
            >
                ⬇ CSV
            </button>
            <button
                id="export-png-btn"
                onClick={handleExportPNG}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-gray-600 bg-white border border-gray-300 rounded-lg hover:border-purple-400 hover:text-purple-700 transition-colors"
            >
                🖼 PNG
            </button>
        </div>
    );
}
