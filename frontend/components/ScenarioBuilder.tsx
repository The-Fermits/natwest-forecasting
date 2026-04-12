'use client';

import React, { useState } from 'react';
import {
    ComposedChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts';
import { fetchScenario } from '@/lib/api';
import type { ForecastPoint } from '@/lib/types';
import { formatNumber, formatDate } from '@/lib/utils';

interface Props {
    baseForecast: ForecastPoint[];
    horizonWeeks: number;
    metricLabel: string;
}

export default function ScenarioBuilder({ baseForecast, horizonWeeks, metricLabel }: Props) {
    const [expanded, setExpanded] = useState(false);
    const [growthRate, setGrowthRate] = useState(0);
    const [removeOutliers, setRemoveOutliers] = useState(false);
    const [seasonalBoostWeek, setSeasonalBoostWeek] = useState<number | null>(null);
    const [seasonalBoostPct, setSeasonalBoostPct] = useState(0);
    const [scenarioForecast, setScenarioForecast] = useState<ForecastPoint[]>([]);
    const [diffSummary, setDiffSummary] = useState('');
    const [isRunning, setIsRunning] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleRunScenario = async () => {
        setIsRunning(true);
        setError(null);
        try {
            const result = await fetchScenario(
                baseForecast,
                growthRate / 100,
                removeOutliers,
                seasonalBoostWeek
                    ? { week: seasonalBoostWeek, pct: seasonalBoostPct / 100 }
                    : undefined,
            );
            setScenarioForecast(result.scenario_forecast);
            setDiffSummary(result.diff_summary);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Scenario calculation failed.');
        } finally {
            setIsRunning(false);
        }
    };

    const chartData = baseForecast.map((base, i) => ({
        date: base.date,
        baseline: base.central,
        scenario: scenarioForecast[i]?.central,
    }));

    return (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between group"
            >
                <div className="flex items-center gap-3">
                    <span className="text-xl">🔧</span>
                    <div className="text-left">
                        <h3 className="font-bold text-gray-900">Scenario Builder</h3>
                        <p className="text-xs text-gray-500 mt-0.5">Model what-if adjustments to the forecast</p>
                    </div>
                </div>
                <span className="text-gray-400 group-hover:text-gray-600 transition-colors text-lg">
                    {expanded ? '▾' : '▸'}
                </span>
            </button>

            {expanded && (
                <div className="mt-5">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-5">
                        {/* Growth rate */}
                        <div>
                            <label className="block text-xs font-semibold text-gray-600 mb-2">
                                Growth Rate Adjustment: {growthRate > 0 ? `+${growthRate}` : growthRate}%
                            </label>
                            <input
                                id="growth-rate-slider"
                                type="range"
                                min={-20}
                                max={20}
                                step={1}
                                value={growthRate}
                                onChange={(e) => setGrowthRate(Number(e.target.value))}
                                className="w-full accent-purple-600"
                            />
                            <div className="flex justify-between text-xs text-gray-400 mt-1">
                                <span>–20%</span>
                                <span>0%</span>
                                <span>+20%</span>
                            </div>
                        </div>

                        {/* Seasonal boost */}
                        <div>
                            <label className="block text-xs font-semibold text-gray-600 mb-2">
                                Seasonal Boost Week
                            </label>
                            <select
                                id="seasonal-boost-week-select"
                                value={seasonalBoostWeek ?? ''}
                                onChange={(e) => setSeasonalBoostWeek(e.target.value ? Number(e.target.value) : null)}
                                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                            >
                                <option value="">None</option>
                                {Array.from({ length: horizonWeeks }, (_, i) => i + 1).map((w) => (
                                    <option key={w} value={w}>Week {w}</option>
                                ))}
                            </select>
                            {seasonalBoostWeek && (
                                <div className="mt-2">
                                    <label className="text-xs text-gray-500">Boost: {seasonalBoostPct}%</label>
                                    <input
                                        type="range"
                                        min={-20}
                                        max={30}
                                        step={1}
                                        value={seasonalBoostPct}
                                        onChange={(e) => setSeasonalBoostPct(Number(e.target.value))}
                                        className="w-full accent-purple-600 mt-1"
                                    />
                                </div>
                            )}
                        </div>

                        {/* Outlier removal */}
                        <div>
                            <label className="block text-xs font-semibold text-gray-600 mb-2">
                                Data Options
                            </label>
                            <label className="flex items-center gap-2.5 cursor-pointer select-none">
                                <div
                                    id="remove-outliers-toggle"
                                    onClick={() => setRemoveOutliers(!removeOutliers)}
                                    className={`relative w-10 h-5.5 rounded-full transition-colors ${removeOutliers ? 'bg-purple-600' : 'bg-gray-300'
                                        } cursor-pointer`}
                                    style={{ minWidth: '40px', height: '22px' }}
                                >
                                    <div
                                        className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${removeOutliers ? 'translate-x-5' : 'translate-x-0.5'
                                            }`}
                                    />
                                </div>
                                <span className="text-sm text-gray-600">Remove outliers before fitting</span>
                            </label>
                        </div>
                    </div>

                    <button
                        id="run-scenario-btn"
                        onClick={handleRunScenario}
                        disabled={isRunning}
                        className="px-5 py-2.5 bg-purple-700 hover:bg-purple-800 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors text-sm shadow-sm"
                    >
                        {isRunning ? 'Calculating…' : 'Apply Scenario'}
                    </button>

                    {error && (
                        <p className="text-red-600 text-sm mt-3">{error}</p>
                    )}

                    {scenarioForecast.length > 0 && (
                        <div className="mt-6">
                            {/* Side-by-side chart */}
                            <h4 className="text-sm font-semibold text-gray-700 mb-3">
                                Scenario A (Baseline) vs Scenario B (Adjusted)
                            </h4>
                            <ResponsiveContainer width="100%" height={200}>
                                <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                                    <XAxis
                                        dataKey="date"
                                        tick={{ fontSize: 10, fill: '#9ca3af' }}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(d) => new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
                                    />
                                    <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} tickFormatter={(v) => formatNumber(v)} width={80} />
                                    <Tooltip
                                        formatter={(value: number) => formatNumber(value, 2)}
                                        labelFormatter={(l) => formatDate(l as string)}
                                    />
                                    <Line dataKey="baseline" stroke="#5B21B6" strokeWidth={2} dot={false} name="Baseline" />
                                    <Line dataKey="scenario" stroke="#EC4899" strokeWidth={2} strokeDasharray="4 2" dot={false} name="Scenario B" />
                                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                                </ComposedChart>
                            </ResponsiveContainer>

                            {/* Diff summary card */}
                            <div className="mt-4 bg-purple-50 border border-purple-200 rounded-xl p-4 text-sm text-purple-800">
                                {diffSummary}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
