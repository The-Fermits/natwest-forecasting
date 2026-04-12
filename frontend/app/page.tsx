'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { METRIC_LABELS, MetricKey } from '@/lib/types';

const METRICS = Object.entries(METRIC_LABELS) as [MetricKey, string][];

export default function LandingPage() {
    const router = useRouter();
    const [hoveredMetric, setHoveredMetric] = useState<MetricKey | null>(null);

    const handleSelectMetric = (metric: MetricKey) => {
        router.push(`/dashboard?metric=${metric}`);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-950 via-purple-900 to-indigo-950 flex flex-col">
            {/* Header */}
            <header className="border-b border-white/10 px-8 py-5">
                <div className="max-w-6xl mx-auto flex items-center gap-3">
                    <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center shadow-lg">
                        <span className="text-purple-700 font-black text-lg">N</span>
                    </div>
                    <div>
                        <span className="text-white font-bold text-lg tracking-tight">NatWest</span>
                        <span className="text-purple-300 font-medium text-lg ml-1">Forecasting</span>
                    </div>
                    <div className="ml-auto">
                        <span className="px-2.5 py-1 bg-purple-500/20 border border-purple-400/30 rounded-full text-purple-200 text-xs font-medium">
                            AI Predictive Analytics
                        </span>
                    </div>
                </div>
            </header>

            {/* Hero */}
            <main className="flex-1 flex flex-col items-center justify-center px-8 py-16">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/20 border border-purple-400/30 rounded-full text-purple-200 text-sm font-medium mb-8">
                        <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                        NatWest Code for Purpose — India Hackathon 2024
                    </div>

                    <h1 className="text-5xl md:text-6xl font-extrabold text-white mb-6 leading-tight tracking-tight">
                        AI-Powered
                        <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-300 to-pink-300">
                            Banking Forecasts
                        </span>
                    </h1>

                    <p className="text-xl text-purple-200 mb-12 max-w-2xl mx-auto leading-relaxed">
                        Transform historical financial data into 1–6 week forecasts with confidence intervals,
                        anomaly detection, scenario comparison, and plain-English AI briefings.
                    </p>

                    {/* Metric cards */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-10">
                        {METRICS.map(([key, label]) => (
                            <button
                                key={key}
                                id={`metric-card-${key}`}
                                onClick={() => handleSelectMetric(key)}
                                onMouseEnter={() => setHoveredMetric(key)}
                                onMouseLeave={() => setHoveredMetric(null)}
                                className={`
                  relative p-5 bg-white/10 border rounded-2xl text-left transition-all duration-200
                  hover:bg-white/20 hover:border-purple-400/60 hover:scale-[1.02] hover:shadow-xl
                  ${hoveredMetric === key ? 'border-purple-400/60' : 'border-white/20'}
                  cursor-pointer group
                `}
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <span className="text-2xl">{METRIC_ICONS[key]}</span>
                                    <span className="opacity-0 group-hover:opacity-100 transition-opacity text-purple-300 text-sm font-medium">
                                        →
                                    </span>
                                </div>
                                <div className="text-white font-semibold text-sm leading-snug">{label}</div>
                                <div className="text-purple-300 text-xs mt-1 opacity-80">104-week dataset</div>
                            </button>
                        ))}
                    </div>

                    <p className="text-purple-400 text-sm">
                        Or{' '}
                        <button
                            onClick={() => router.push('/dashboard?mode=upload')}
                            className="text-purple-300 hover:text-white underline underline-offset-2 transition-colors"
                        >
                            upload your own CSV
                        </button>{' '}
                        to forecast your data
                    </p>
                </div>
            </main>

            {/* Feature pills */}
            <footer className="border-t border-white/10 px-8 py-6">
                <div className="max-w-6xl mx-auto flex flex-wrap justify-center gap-3">
                    {[
                        '✦ Prophet & AutoETS Models',
                        '✦ 80% / 95% Confidence Bands',
                        '✦ Anomaly Detection',
                        '✦ Scenario Builder',
                        '✦ Claude AI Briefings',
                        '✦ CSV Export',
                    ].map((f) => (
                        <span
                            key={f}
                            className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-full text-purple-300 text-xs font-medium"
                        >
                            {f}
                        </span>
                    ))}
                </div>
            </footer>
        </div>
    );
}

const METRIC_ICONS: Record<MetricKey, string> = {
    transaction_volume: '💳',
    loan_disbursements: '🏦',
    default_rates: '⚠️',
    new_signups: '👥',
    churn_rate: '📉',
    support_tickets: '🎫',
};
