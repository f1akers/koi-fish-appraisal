/**
 * CameraCapture Component
 * 
 * Camera interface for capturing koi fish images.
 * Flat design with gradient accents.
 */

import { useEffect } from 'react';
import { useCamera } from '../hooks/useCamera';
import { GuideOverlay } from './GuideOverlay';

interface CameraCaptureProps {
    onCapture: (imageBlob: Blob) => void;
    isProcessing: boolean;
}

export function CameraCapture({ onCapture, isProcessing }: CameraCaptureProps) {
    const { videoRef, state, startCamera, stopCamera, captureImage, switchCamera } = useCamera();

    useEffect(() => {
        startCamera();
        return () => stopCamera();
    }, []);

    const handleCapture = async () => {
        const blob = await captureImage();
        if (blob) {
            onCapture(blob);
        }
    };

    // Error state with flat design
    if (state.error) {
        return (
            <div className="flex flex-col items-center justify-center h-96 bg-gradient-to-br from-red-50 to-orange-50 rounded-3xl p-8">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-red-400 to-red-500 flex items-center justify-center mb-6">
                    <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                </div>
                <p className="text-lg font-semibold text-gray-800 mb-2">Camera Access Required</p>
                <p className="text-gray-600 text-center mb-6 max-w-sm">{state.error}</p>
                <button
                    onClick={startCamera}
                    className="btn-flat btn-primary"
                >
                    Try Again
                </button>
            </div>
        );
    }

    return (
        <div className="relative w-full max-w-2xl mx-auto">
            {/* Camera Preview Container */}
            <div className="relative aspect-[4/3] bg-gray-900 rounded-3xl overflow-hidden">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                />

                {/* Guide Overlay */}
                {state.isActive && <GuideOverlay />}

                {/* Processing Overlay */}
                {isProcessing && (
                    <div className="absolute inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center">
                        <div className="text-center">
                            <div className="relative w-16 h-16 mx-auto mb-4">
                                <div className="absolute inset-0 rounded-full border-4 border-white/20"></div>
                                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-white animate-spin"></div>
                            </div>
                            <p className="text-white font-medium">Analyzing your koi...</p>
                            <p className="text-white/60 text-sm mt-1">This may take a few seconds</p>
                        </div>
                    </div>
                )}

                {/* Camera inactive overlay */}
                {!state.isActive && !isProcessing && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                        <div className="text-center">
                            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/10 flex items-center justify-center animate-pulse-soft">
                                <svg className="w-8 h-8 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <p className="text-white/60">Initializing camera...</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Control Panel - Flat design */}
            <div className="mt-6 flex flex-col items-center gap-4">
                {/* Main controls */}
                <div className="flex items-center gap-4">
                    {/* Switch Camera Button */}
                    <button
                        onClick={switchCamera}
                        disabled={isProcessing}
                        className="w-14 h-14 rounded-2xl bg-gray-100 hover:bg-gray-200 transition-all duration-200 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label="Switch camera"
                    >
                        <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                    </button>

                    {/* Capture Button - Gradient style */}
                    <button
                        onClick={handleCapture}
                        disabled={!state.isActive || isProcessing}
                        className="w-20 h-20 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 transition-all duration-200 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
                        aria-label="Capture image"
                    >
                        <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center">
                            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                        </div>
                    </button>

                    {/* Placeholder for symmetry */}
                    <div className="w-14 h-14"></div>
                </div>

                {/* Status text */}
                <p className="text-gray-500 text-sm">
                    {isProcessing ? 'Processing...' : state.isActive ? 'Tap to capture' : 'Starting camera...'}
                </p>
            </div>

            {/* Tips Card */}
            <div className="mt-8 p-4 bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl">
                <div className="flex gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center flex-shrink-0">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                    </div>
                    <div>
                        <p className="font-semibold text-gray-800 text-sm">Tips for best results</p>
                        <p className="text-gray-600 text-sm mt-1">
                            Use good lighting, keep the camera steady, and ensure both the koi fish and reference coin are fully visible in the frame.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
