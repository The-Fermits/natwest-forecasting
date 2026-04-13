'use client';

import React, { useEffect, useRef, useState } from 'react';
import { buildBriefingUrl } from '@/lib/api';
import type { MetricKey } from '@/lib/types';

interface Props {
    metric: MetricKey;
    metricLabel: string;
    trend: string;
    horizonWeeks: number;
    anomalyCount: number;
    forecastSummary: string;
    modelUsed: string;
    trigger: number; // Increment to re-fetch briefing
}

export default function AIBriefingCard({
    metric,
    metricLabel,
    trend,
    horizonWeeks,
    anomalyCount,
    forecastSummary,
    modelUsed,
    trigger,
}: Props) {
    const [briefingText, setBriefingText] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showPrompt, setShowPrompt] = useState(false);
    const eventSourceRef = useRef<EventSource | null>(null);

    useEffect(() => {
        if (trigger === 0) return;

        // Close any existing stream before starting a new one
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        setBriefingText('');
        setIsStreaming(true);
        setError(null);

        const url = buildBriefingUrl({
            metric: metricLabel,
            trend,
            horizon: horizonWeeks,
            anomalyCount,
            forecastSummary,
            modelUsed,
        });

        const es = new EventSource(url);
        eventSourceRef.current = es;

        es.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.done) {
                    setIsStreaming(false);
                    es.close();
                } else if (data.token) {
                    setBriefingText((prev) => prev + data.token);
                } else if (data.error) {
                    setError(data.error);
                    setIsStreaming(false);
                    es.close();
                }
            } catch {
                // Silently skip malformed SSE events
            }
        };

        es.onerror = () => {
            setError('Failed to connect to AI briefing service.');
            setIsStreaming(false);
            es.close();
        };

        return () => {
            es.close();
        };
    }, [trigger]); // eslint-disable-line react-hooks/exhaustive-deps

    return (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 h-full">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
                        <span className="text-white text-xs font-bold">C</span>
                    </div>
                    <div>
                        <h3 className="font-bold text-gray-900 text-sm">AI Briefing</h3>
                        <p className="text-xs text-gray-400">Powered by Gemini</p>
                    </div>
                </div>
                {isStreaming && (
                    <div className="flex items-center gap-1.5 text-xs text-purple-600 font-medium">
                        <span className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
                        Generating…
                    </div>
                )}
            </div>

            {error ? (
                <div className="text-sm text-red-600 bg-red-50 rounded-lg p-3">
                    ⚠ {error}
                </div>
            ) : (
                <div className="text-sm text-gray-700 leading-relaxed min-h-[80px]">
                    {briefingText || (isStreaming ? (
                        <span className="text-gray-400 italic">Analysing your data…</span>
                    ) : (
                        <span className="text-gray-400 italic">Briefing will appear here after forecast runs.</span>
                    ))}
                    {isStreaming && briefingText && (
                        <span className="inline-block w-0.5 h-4 bg-purple-500 ml-0.5 animate-pulse" />
                    )}
                </div>
            )}

            {/* Expandable prompt transparency */}
            <div className="mt-4 border-t border-gray-100 pt-3">
                <button
                    onClick={() => setShowPrompt(!showPrompt)}
                    className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 transition-colors"
                >
                    <span>{showPrompt ? '▾' : '▸'}</span>
                    How was this generated?
                </button>
                {showPrompt && (
                    <div className="mt-2 bg-gray-50 rounded-lg p-3 text-xs text-gray-600 font-mono leading-relaxed border border-gray-200">
                        <p><strong>Model:</strong> Gemini 1.5 Flash</p>
                        <p><strong>Context:</strong> Metric={metricLabel}, Trend={trend}, Horizon={horizonWeeks}w, Anomalies={anomalyCount}</p>
                        <p><strong>Instructions:</strong> 3–5 sentences, plain English for non-technical banking manager. Cover trend, uncertainty, anomalies, and one recommendation.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
