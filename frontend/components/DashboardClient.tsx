'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { fetchForecast, uploadCSV } from '@/lib/api';
import type {
    ForecastResponse,
    MetricKey,
    ConfidenceLevel,
    DataMode,
    UploadResponse,
} from '@/lib/types';
import { METRIC_LABELS } from '@/lib/types';
import { buildForecastSummary } from '@/lib/utils';
import ForecastChart from './ForecastChart';
import DataModeSelector from './DataModeSelector';
import MetricSelector from './MetricSelector';
import HorizonSlider from './HorizonSlider';
import ConfidenceBandToggle from './ConfidenceBandToggle';
import AnomalyPanel from './AnomalyPanel';
import ScenarioBuilder from './ScenarioBuilder';
import AIBriefingCard from './AIBriefingCard';
import TransparencyPanel from './TransparencyPanel';
import DataQualityChecklist from './DataQualityChecklist';
import ModelAccuracyPanel from './ModelAccuracyPanel';
import ExportButtons from './ExportButtons';
import CSVUploader from './CSVUploader';

const PROGRESS_STEPS = [
    'Validating data...',
    'Fitting model...',
    'Detecting anomalies...',
    'Generating AI briefing...',
];

export default function DashboardClient() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const initialMetric = (searchParams.get('metric') || 'transaction_volume') as MetricKey;
    const initialMode = (searchParams.get('mode') || 'default') as DataMode;

    const [dataMode, setDataMode] = useState<DataMode>(initialMode);
    const [metric, setMetric] = useState<MetricKey>(initialMetric);
    const [sessionId, setSessionId] = useState<string | undefined>();
    const [uploadMeta, setUploadMeta] = useState<UploadResponse | null>(null);
    const [horizonWeeks, setHorizonWeeks] = useState(4);
    const [confidenceLevel, setConfidenceLevel] = useState<ConfidenceLevel>(0.80);

    const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [loadingStep, setLoadingStep] = useState(0);
    const [error, setError] = useState<string | null>(null);

    const [briefingTrigger, setBriefingTrigger] = useState(0);

    const runForecast = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        setLoadingStep(0);

        // Simulate multi-step progress for UX — steps 1–3 are near-instantaneous
        // in practice, but we animate them so the user sees what's happening.
        const stepTimers = [
            setTimeout(() => setLoadingStep(1), 400),
            setTimeout(() => setLoadingStep(2), 900),
            setTimeout(() => setLoadingStep(3), 1400),
        ];

        try {
            const result = await fetchForecast(
                metric,
                horizonWeeks,
                confidenceLevel,
                dataMode === 'upload' ? sessionId : undefined,
            );
            setForecastData(result);
            setBriefingTrigger((t) => t + 1);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'An unexpected error occurred.');
        } finally {
            stepTimers.forEach(clearTimeout);
            setIsLoading(false);
        }
    }, [metric, horizonWeeks, confidenceLevel, dataMode, sessionId]);

    // Auto-run forecast on mount for default mode
    useEffect(() => {
        if (dataMode === 'default') {
            runForecast();
        }
    }, [metric, horizonWeeks, confidenceLevel]); // eslint-disable-line react-hooks/exhaustive-deps

    const handleUploadComplete = useCallback((meta: UploadResponse) => {
        setUploadMeta(meta);
        setSessionId(meta.session_id);
    }, []);

    const handleUploadForecast = useCallback(() => {
        if (sessionId) runForecast();
    }, [sessionId, runForecast]);

    const forecastSummary = forecastData
        ? buildForecastSummary(
            forecastData.forecast,
            forecastData.historical[forecastData.historical.length - 1]?.value ?? 0,
        )
        : '';

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Top navbar */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
                <div className="max-w-screen-2xl mx-auto px-6 py-3 flex items-center gap-4">
                    <button
                        onClick={() => router.push('/')}
                        className="flex items-center gap-2.5 group"
                    >
                        <div className="w-8 h-8 bg-purple-700 rounded-lg flex items-center justify-center shadow">
                            <span className="text-white font-black text-sm">N</span>
                        </div>
                        <span className="font-bold text-purple-700 text-base tracking-tight group-hover:text-purple-900 transition-colors">
                            NatWest Forecasting
                        </span>
                    </button>

                    <div className="h-5 w-px bg-gray-300 mx-1" />

                    <div className="flex items-center gap-3 flex-1">
                        <DataModeSelector mode={dataMode} onModeChange={setDataMode} />
                        {dataMode === 'default' && (
                            <MetricSelector value={metric} onChange={setMetric} />
                        )}
                    </div>

                    <div className="flex items-center gap-3">
                        <HorizonSlider value={horizonWeeks} onChange={setHorizonWeeks} />
                        <ConfidenceBandToggle value={confidenceLevel} onChange={setConfidenceLevel} />
                        {forecastData && (
                            <ExportButtons forecastData={forecastData} metricLabel={forecastData.metric_label} />
                        )}
                    </div>
                </div>
            </header>

            <main className="max-w-screen-2xl mx-auto px-6 py-6 space-y-6">
                {/* Upload mode panel */}
                {dataMode === 'upload' && (
                    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                        <CSVUploader
                            onUploadComplete={handleUploadComplete}
                            uploadMeta={uploadMeta}
                        />
                        {uploadMeta && (
                            <div className="mt-4 flex justify-end">
                                <button
                                    id="run-forecast-upload-btn"
                                    onClick={handleUploadForecast}
                                    disabled={isLoading}
                                    className="px-5 py-2.5 bg-purple-700 hover:bg-purple-800 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors shadow-sm"
                                >
                                    {isLoading ? 'Running…' : 'Run Forecast'}
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* Progress indicator */}
                {isLoading && (
                    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                        <div className="flex flex-col items-center gap-4">
                            <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
                            <div className="flex flex-col gap-2 w-full max-w-sm">
                                {PROGRESS_STEPS.map((step, i) => (
                                    <div key={step} className="flex items-center gap-3">
                                        <div
                                            className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold transition-all ${i < loadingStep
                                                    ? 'bg-emerald-500 text-white'
                                                    : i === loadingStep
                                                        ? 'bg-purple-600 text-white animate-pulse-step'
                                                        : 'bg-gray-200 text-gray-400'
                                                }`}
                                        >
                                            {i < loadingStep ? '✓' : i + 1}
                                        </div>
                                        <span
                                            className={`text-sm font-medium ${i === loadingStep ? 'text-purple-700' : i < loadingStep ? 'text-emerald-600' : 'text-gray-400'
                                                }`}
                                        >
                                            {step}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Error state */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-2xl p-5">
                        <div className="flex gap-3 items-start">
                            <span className="text-red-500 text-xl">⚠</span>
                            <div>
                                <p className="font-semibold text-red-700">Forecast Error</p>
                                <p className="text-red-600 text-sm mt-1">{error}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Main forecast results */}
                {forecastData && !isLoading && (
                    <>
                        {/* Data Quality */}
                        <DataQualityChecklist checks={forecastData.data_quality} />

                        {/* Main chart */}
                        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6" id="forecast-chart-container">
                            <div className="mb-4 flex items-center justify-between">
                                <div>
                                    <h2 className="text-lg font-bold text-gray-900">{forecastData.metric_label}</h2>
                                    <p className="text-sm text-gray-500 mt-0.5">
                                        {forecastData.training_range.period_count} weeks history →{' '}
                                        {horizonWeeks}-week forecast
                                    </p>
                                </div>
                                <div className="flex items-center gap-1.5 text-sm text-gray-500">
                                    <span className="w-3 h-0.5 bg-gray-400 inline-block rounded" />
                                    Historical
                                    <span className="w-3 h-0.5 bg-purple-600 inline-block rounded ml-2" />
                                    Forecast
                                    <span className="w-3 h-0.5 bg-amber-500 inline-block rounded ml-2 border-dashed" />
                                    Naive
                                    <span className="w-3 h-0.5 bg-emerald-500 inline-block rounded ml-2 border-dashed" />
                                    MA(4)
                                </div>
                            </div>
                            <ForecastChart
                                historical={forecastData.historical}
                                forecast={forecastData.forecast}
                                baselineNaive={forecastData.baseline_naive}
                                baselineMA={forecastData.baseline_ma}
                                anomalies={forecastData.anomalies}
                                confidenceLevel={forecastData.confidence_level}
                            />
                        </div>

                        {/* Bottom panels row */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            <ModelAccuracyPanel
                                accuracy={forecastData.accuracy}
                                modelUsed={forecastData.model_used}
                            />
                            <div className="lg:col-span-2">
                                <AIBriefingCard
                                    metric={metric}
                                    metricLabel={forecastData.metric_label}
                                    trend={forecastData.patterns.trend}
                                    horizonWeeks={horizonWeeks}
                                    anomalyCount={forecastData.anomalies.length}
                                    forecastSummary={forecastSummary}
                                    modelUsed={forecastData.model_used}
                                    trigger={briefingTrigger}
                                />
                            </div>
                        </div>

                        {/* Anomaly panel */}
                        {forecastData.anomalies.length > 0 && (
                            <AnomalyPanel
                                anomalies={forecastData.anomalies}
                                metricLabel={forecastData.metric_label}
                            />
                        )}

                        {/* Scenario builder */}
                        <ScenarioBuilder
                            baseForecast={forecastData.forecast}
                            horizonWeeks={horizonWeeks}
                            metricLabel={forecastData.metric_label}
                        />

                        {/* Transparency panel */}
                        <TransparencyPanel
                            modelUsed={forecastData.model_used}
                            trainingRange={forecastData.training_range}
                            confidenceLevel={forecastData.confidence_level}
                            accuracy={forecastData.accuracy}
                            patterns={forecastData.patterns}
                        />
                    </>
                )}
            </main>
        </div>
    );
}
