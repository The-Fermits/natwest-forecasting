'use client';

import { Suspense } from 'react';
import dynamic from 'next/dynamic';

// Dynamic import to avoid SSR issues with browser-only libraries (Recharts, EventSource)
const Dashboard = dynamic(() => import('@/components/DashboardClient'), { ssr: false });

export default function DashboardPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-gray-500 text-sm">Loading dashboard…</p>
                </div>
            </div>
        }>
            <Dashboard />
        </Suspense>
    );
}
