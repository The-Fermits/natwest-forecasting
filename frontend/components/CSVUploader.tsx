'use client';

import React, { useCallback, useState } from 'react';
import { uploadCSV } from '@/lib/api';
import type { UploadResponse } from '@/lib/types';

interface Props {
    onUploadComplete: (meta: UploadResponse) => void;
    uploadMeta: UploadResponse | null;
}

export default function CSVUploader({ onUploadComplete, uploadMeta }: Props) {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFile = useCallback(async (file: File) => {
        if (!file.name.endsWith('.csv')) {
            setError('Please upload a CSV file.');
            return;
        }
        setIsUploading(true);
        setError(null);
        try {
            const meta = await uploadCSV(file);
            onUploadComplete(meta);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Upload failed.');
        } finally {
            setIsUploading(false);
        }
    }, [onUploadComplete]);

    const onDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    }, [handleFile]);

    return (
        <div>
            <label
                htmlFor="csv-file-input"
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={onDrop}
                className={`flex flex-col items-center justify-center border-2 border-dashed rounded-2xl p-10 cursor-pointer transition-all ${isDragging
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-300 bg-gray-50 hover:border-purple-400 hover:bg-purple-50/50'
                    }`}
            >
                <span className="text-3xl mb-2">📁</span>
                <p className="font-semibold text-gray-700">
                    {isUploading ? 'Uploading…' : 'Drop your CSV here or click to browse'}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                    Required: one date column + one numeric value column. Min 12 weekly periods.
                </p>
                <input
                    id="csv-file-input"
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                />
            </label>

            {error && (
                <p className="text-red-600 text-sm mt-3 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                    {error}
                </p>
            )}

            {uploadMeta && (
                <div className="mt-4">
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-emerald-500">✓</span>
                        <span className="text-sm font-semibold text-gray-700">
                            Upload successful — {uploadMeta.period_count} weekly periods detected
                        </span>
                    </div>
                    <div className="text-xs text-gray-500 mb-3">
                        Date column: <code className="bg-gray-100 px-1 rounded">{uploadMeta.detected_date_col}</code> &nbsp;
                        Value column: <code className="bg-gray-100 px-1 rounded">{uploadMeta.detected_value_col}</code>
                    </div>

                    {/* Preview table */}
                    <div className="overflow-x-auto rounded-lg border border-gray-200">
                        <table className="text-xs w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    {Object.keys(uploadMeta.preview[0] || {}).map((col) => (
                                        <th key={col} className="text-left px-3 py-2 text-gray-600 font-semibold">{col}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {uploadMeta.preview.map((row, i) => (
                                    <tr key={i} className="border-t border-gray-100">
                                        {Object.values(row).map((v, j) => (
                                            <td key={j} className="px-3 py-2 text-gray-700">{String(v)}</td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
