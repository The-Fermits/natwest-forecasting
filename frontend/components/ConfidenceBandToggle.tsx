'use client';

import React from 'react';
import type { ConfidenceLevel } from '@/lib/types';

interface Props {
    value: ConfidenceLevel;
    onChange: (level: ConfidenceLevel) => void;
}

export default function ConfidenceBandToggle({ value, onChange }: Props) {
    return (
        <div className="flex bg-gray-100 rounded-lg p-0.5 gap-0.5">
            <button
                id="confidence-80-btn"
                onClick={() => onChange(0.80)}
                className={`px-2.5 py-1.5 text-xs font-semibold rounded-md transition-all ${value === 0.80 ? 'bg-white text-purple-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
            >
                80% CI
            </button>
            <button
                id="confidence-95-btn"
                onClick={() => onChange(0.95)}
                className={`px-2.5 py-1.5 text-xs font-semibold rounded-md transition-all ${value === 0.95 ? 'bg-white text-purple-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
            >
                95% CI
            </button>
        </div>
    );
}
