'use client';

import React from 'react';

interface Props {
    value: number;
    onChange: (weeks: number) => void;
}

export default function HorizonSlider({ value, onChange }: Props) {
    return (
        <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-gray-500 whitespace-nowrap">
                Horizon: {value}w
            </label>
            <input
                id="horizon-slider"
                type="range"
                min={1}
                max={6}
                step={1}
                value={value}
                onChange={(e) => onChange(Number(e.target.value))}
                className="w-20 accent-purple-600"
            />
        </div>
    );
}
