/**
 * ResultsPanel Component
 * 
 * Display appraisal results with metrics and actions.
 */

import type { AppraisalResult } from '../types';
import { MetricCard } from './MetricCard';

interface ResultsPanelProps {
    result: AppraisalResult;
    imagePreview: string | null;
    onNewCapture: () => void;
    onExport: () => void;
}

export function ResultsPanel({ result, imagePreview, onNewCapture, onExport }: ResultsPanelProps) {
    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('en-PH', {
            style: 'currency',
            currency: 'PHP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(price);
    };

    const patternDisplay = result.pattern_name.charAt(0).toUpperCase() + result.pattern_name.slice(1);

    return (
        <div className="w-full max-w-4xl mx-auto p-4">
            {/* Header with Price */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg p-6 mb-6">
                <h2 className="text-lg font-medium mb-2">Predicted Price</h2>
                <p className="text-4xl font-bold">{formatPrice(result.predicted_price)}</p>
            </div>

            {/* Image and Metrics Grid */}
            <div className="grid md:grid-cols-2 gap-6 mb-6">
                {/* Image Preview */}
                {imagePreview && (
                    <div className="bg-gray-100 rounded-lg overflow-hidden">
                        <img
                            src={imagePreview}
                            alt="Captured koi fish"
                            className="w-full h-64 object-cover"
                        />
                    </div>
                )}

                {/* Quick Metrics */}
                <div className="grid grid-cols-2 gap-4">
                    <MetricCard
                        title="Size"
                        value={`${result.size_cm.toFixed(1)} cm`}
                        icon={
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                            </svg>
                        }
                    />
                    <MetricCard
                        title="Pattern"
                        value={patternDisplay}
                        subtitle={`${(result.pattern_confidence * 100).toFixed(0)}% confidence`}
                        icon={
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                            </svg>
                        }
                    />
                    <MetricCard
                        title="Symmetry"
                        value={`${(result.symmetry_score * 100).toFixed(0)}%`}
                        color={result.symmetry_score >= 0.8 ? 'success' : result.symmetry_score >= 0.6 ? 'warning' : 'default'}
                        icon={
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                            </svg>
                        }
                    />
                    <MetricCard
                        title="Color Quality"
                        value={`${(result.color_quality_score * 100).toFixed(0)}%`}
                        color={result.color_quality_score >= 0.8 ? 'success' : result.color_quality_score >= 0.6 ? 'warning' : 'default'}
                        icon={
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                            </svg>
                        }
                    />
                </div>
            </div>

            {/* Color Distribution */}
            <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
                <h3 className="text-sm font-medium text-gray-600 mb-4">Color Distribution</h3>
                <div className="space-y-3">
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span>White</span>
                            <span>{result.color_white_pct.toFixed(1)}%</span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gray-400"
                                style={{ width: `${result.color_white_pct}%` }}
                            ></div>
                        </div>
                    </div>
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span>Red</span>
                            <span>{result.color_red_pct.toFixed(1)}%</span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-red-500"
                                style={{ width: `${result.color_red_pct}%` }}
                            ></div>
                        </div>
                    </div>
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span>Black</span>
                            <span>{result.color_black_pct.toFixed(1)}%</span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gray-900"
                                style={{ width: `${result.color_black_pct}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
                <button
                    onClick={onExport}
                    className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                >
                    Export to CSV
                </button>
                <button
                    onClick={onNewCapture}
                    className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                    New Capture
                </button>
            </div>
        </div>
    );
}
