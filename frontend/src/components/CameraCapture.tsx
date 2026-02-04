/**
 * CameraCapture Component
 * 
 * Camera interface for capturing koi fish images.
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

    if (state.error) {
        return (
            <div className="flex flex-col items-center justify-center h-96 bg-gray-100 rounded-lg p-8">
                <div className="text-red-500 text-center mb-4">
                    <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <p className="text-lg font-medium">{state.error}</p>
                </div>
                <button
                    onClick={startCamera}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                    Try Again
                </button>
            </div>
        );
    }

    return (
        <div className="relative w-full max-w-2xl mx-auto">
            {/* Video Preview */}
            <div className="relative aspect-[4/3] bg-black rounded-lg overflow-hidden">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                />

                {/* Guide Overlay */}
                {state.isActive && <GuideOverlay />}

                {/* Loading Overlay */}
                {isProcessing && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                        <div className="text-white text-center">
                            <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                            <p>Processing image...</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Controls */}
            <div className="flex justify-center gap-4 mt-4">
                {/* Switch Camera Button */}
                <button
                    onClick={switchCamera}
                    disabled={isProcessing}
                    className="p-3 bg-gray-200 rounded-full hover:bg-gray-300 transition disabled:opacity-50"
                    aria-label="Switch camera"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                </button>

                {/* Capture Button */}
                <button
                    onClick={handleCapture}
                    disabled={!state.isActive || isProcessing}
                    className="px-8 py-3 bg-blue-600 text-white text-lg font-medium rounded-full hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isProcessing ? 'Processing...' : 'Capture'}
                </button>
            </div>

            {/* Instructions */}
            <p className="text-center text-gray-600 mt-4 text-sm">
                Position the koi fish and reference coin clearly in the frame, then tap Capture.
            </p>
        </div>
    );
}
