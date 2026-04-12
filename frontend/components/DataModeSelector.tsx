'use client';

import React from 'react';
import type { DataMode } from '@/lib/types';

interface Props {
    mode: DataMode;
    onModeChange: (mode: DataMode) => void;
}

export default function DataModeSelector({ mode, onModeChange }: Props) {
    return (
        <div className="flex bg-gray-100 rounded-lg p-0.5 gap-0.5">
            <button
                id="mode-default-btn"
                onClick={() => onModeChange('default')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${mode === 'default'
                        ? 'bg-white text-purple-700 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
            >
                Default Datasets
            </button>
            <button
                id="mode-upload-btn"
                onClick={() => onModeChange('upload')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${mode === 'upload'
                        ? 'bg-white text-purple-700 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
            >
                Upload CSV
            </button>
        </div>
    );
}
