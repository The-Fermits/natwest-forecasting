import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'NatWest AI Forecasting Dashboard',
    description:
        'AI-powered predictive forecasting for NatWest banking operations teams. ' +
        'Short-term forecasts, anomaly detection, scenario comparison, and Claude AI briefings.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <head>
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
                <link
                    href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
                    rel="stylesheet"
                />
            </head>
            <body className="min-h-screen bg-gray-50 font-sans antialiased">{children}</body>
        </html>
    );
}
