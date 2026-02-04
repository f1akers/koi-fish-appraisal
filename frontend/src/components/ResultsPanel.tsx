/**
 * ResultsPanel Component
 * 
 * Display appraisal results with flat gradient design.
 */

import type { AppraisalResult } from '../types';
import { MetricCard } from './MetricCard';
import { ColorDistribution } from './ColorDistribution';

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
        <div className="w-full max-w-4xl mx-auto">
            {/* Price Hero Card - Gradient */}
            <div className="bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 rounded-3xl p-8 mb-8 animate-fade-in">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <span className="text-white/80 font-medium">Estimated Value</span>
                </div>
                <p className="text-5xl font-bold text-white animate-count">
                    {formatPrice(result.predicted_price)}
                </p>
                <p className="text-white/60 text-sm mt-3">
                    Based on size, pattern, color, and symmetry analysis
                </p>
            </div>

            {/* Image and Quick Stats */}
            <div className="grid lg:grid-cols-5 gap-6 mb-8">
                {/* Image Preview */}
                {imagePreview && (
                    <div className="lg:col-span-2 animate-fade-in animate-delay-100">
                        <div className="relative rounded-2xl overflow-hidden bg-gray-100">
                            <img
                                src={imagePreview}
                                alt="Captured koi fish"
                                className="w-full aspect-[4/3] object-cover"
                            />
                            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/50 to-transparent p-4">
                                <span className="text-white/80 text-sm">Captured Image</span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Metrics Grid */}
                <div className={`grid grid-cols-2 gap-4 ${imagePreview ? 'lg:col-span-3' : 'lg:col-span-5'}`}>
                    <div className="animate-fade-in animate-delay-100">
                        <MetricCard
                            title="Size"
                            value={`${result.size_cm.toFixed(1)} cm`}
                            variant="info"
                            icon={
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                                </svg>
                            }
                        />
                    </div>
                    <div className="animate-fade-in animate-delay-200">
                        <MetricCard
                            title="Pattern"
                            value={patternDisplay}
                            subtitle={`${(result.pattern_confidence * 100).toFixed(0)}% confidence`}
                            variant="gold"
                            icon={
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                                </svg>
                            }
                        />
                    </div>
                    <div className="animate-fade-in animate-delay-300">
                        <MetricCard
                            title="Symmetry"
                            value={`${(result.symmetry_score * 100).toFixed(0)}%`}
                            subtitle={result.symmetry_score >= 0.8 ? 'Excellent' : result.symmetry_score >= 0.6 ? 'Good' : 'Fair'}
                            variant={result.symmetry_score >= 0.8 ? 'success' : result.symmetry_score >= 0.6 ? 'warning' : 'default'}
                            icon={
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                                </svg>
                            }
                        />
                    </div>
                    <div className="animate-fade-in animate-delay-400">
                        <MetricCard
                            title="Color Quality"
                            value={`${(result.color_quality_score * 100).toFixed(0)}%`}
                            subtitle={result.color_quality_score >= 0.8 ? 'Premium' : result.color_quality_score >= 0.6 ? 'Standard' : 'Basic'}
                            variant={result.color_quality_score >= 0.8 ? 'success' : result.color_quality_score >= 0.6 ? 'warning' : 'default'}
                            icon={
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                                </svg>
                            }
                        />
                    </div>
                </div>
            </div>

            {/* Color Distribution Card */}
            <div className="bg-gradient-to-br from-gray-50 to-slate-100 rounded-2xl p-6 mb-8 animate-fade-in animate-delay-300">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-400 to-pink-500 flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800">Color Distribution</h3>
                </div>
                <ColorDistribution
                    white={result.color_white_pct}
                    red={result.color_red_pct}
                    black={result.color_black_pct}
                />
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 animate-fade-in animate-delay-400">
                <button
                    onClick={onExport}
                    className="flex-1 px-6 py-4 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-2xl transition-all duration-200 flex items-center justify-center gap-2"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Export to CSV
                </button>
                <button
                    onClick={onNewCapture}
                    className="flex-1 px-6 py-4 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white font-semibold rounded-2xl transition-all duration-200 flex items-center justify-center gap-2"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    New Capture
                </button>
            </div>
        </div>
    );
}
