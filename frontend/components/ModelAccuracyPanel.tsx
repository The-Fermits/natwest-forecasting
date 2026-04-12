'use client';

import React from 'react';
import type { ModelAccuracy } from '@/lib/types';
import { formatPercent, formatNumber } from '@/lib/utils';

interface Props {
    accuracy: ModelAccuracy;
    modelUsed: string;
}

export default function ModelAccuracyPanel({ accuracy, modelUsed }: Props) {
    const outperforms = accuracy.outperformance_pct > 0;

    return (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">📊</span>
                <h3 className="font-bold text-gray-900">Model Accuracy</h3>
            </div>

            {/* AI Model metrics */}
            <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-purple-700 uppercase tracking-wide">
                        {modelUsed} (AI)
                    </span>
                    <span
                        className={`text-xs font-bold px-2 py-0.5 rounded-full border ${outperforms
                                ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
                                : 'bg-red-100 text-red-700 border-red-200'
                            }`}
                    >
                        {outperforms
                            ? `AI wins +${accuracy.outperformance_pct.toFixed(1)}%`
                            : `Baseline wins ↑`}
                    </span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                    <div className="bg-purple-50 border border-purple-100 rounded-lg p-2.5 text-center">
                        <p className="text-lg font-bold text-purple-700">
                            {accuracy.mape !== null ? formatPercent(accuracy.mape) : '—'}
                        </p>
                        <p className="text-xs text-gray-500">MAPE</p>
                    </div>
                    <div className="bg-purple-50 border border-purple-100 rounded-lg p-2.5 text-center">
                        <p className="text-lg font-bold text-purple-700">
                            {accuracy.rmse !== null ? formatNumber(accuracy.rmse, 0) : '—'}
                        </p>
                        <p className="text-xs text-gray-500">RMSE</p>
                    </div>
                </div>
            </div>

            {/* Baseline metrics */}
            <div className="border-t border-gray-100 pt-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Baselines</p>
                <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                        <span className="flex items-center gap-1.5">
                            <span className="w-5 h-0.5 bg-amber-500 inline-block" />
                            Naive (last value)
                        </span>
                        <span className="text-gray-600 font-medium">
                            MAPE {formatPercent(accuracy.baseline_naive_mape)} | RMSE {formatNumber(accuracy.baseline_naive_rmse, 0)}
                        </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                        <span className="flex items-center gap-1.5">
                            <span className="w-5 h-0.5 bg-emerald-500 inline-block" />
                            MA(4)
                        </span>
                        <span className="text-gray-600 font-medium">
                            MAPE {formatPercent(accuracy.baseline_ma_mape)} | RMSE {formatNumber(accuracy.baseline_ma_rmse, 0)}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
