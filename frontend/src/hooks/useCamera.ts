/**
 * useCamera Hook
 * 
 * Custom hook for managing camera access and capture.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import type { CameraState } from '../types';

interface UseCameraReturn {
    videoRef: React.RefObject<HTMLVideoElement | null>;
    state: CameraState;
    startCamera: () => Promise<void>;
    stopCamera: () => void;
    captureImage: () => Promise<Blob | null>;
    switchCamera: () => void;
}

export function useCamera(): UseCameraReturn {
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const streamRef = useRef<MediaStream | null>(null);

    const [state, setState] = useState<CameraState>({
        isActive: false,
        hasPermission: null,
        facingMode: 'environment',
        error: null,
    });

    const startCamera = useCallback(async () => {
        try {
            setState(prev => ({ ...prev, error: null }));

            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: state.facingMode,
                    width: { ideal: 1920 },
                    height: { ideal: 1080 },
                },
            });

            streamRef.current = stream;

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                await videoRef.current.play();
            }

            setState(prev => ({
                ...prev,
                isActive: true,
                hasPermission: true,
            }));
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to access camera';

            setState(prev => ({
                ...prev,
                isActive: false,
                hasPermission: false,
                error: message.includes('Permission')
                    ? 'Camera permission denied. Please allow camera access.'
                    : 'Failed to access camera. Please check if a camera is connected.',
            }));
        }
    }, [state.facingMode]);

    const stopCamera = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }

        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }

        setState(prev => ({ ...prev, isActive: false }));
    }, []);

    const captureImage = useCallback(async (): Promise<Blob | null> => {
        if (!videoRef.current || !state.isActive) {
            return null;
        }

        const video = videoRef.current;
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
            return null;
        }

        ctx.drawImage(video, 0, 0);

        return new Promise((resolve) => {
            canvas.toBlob(
                (blob) => resolve(blob),
                'image/jpeg',
                0.9
            );
        });
    }, [state.isActive]);

    const switchCamera = useCallback(() => {
        setState(prev => ({
            ...prev,
            facingMode: prev.facingMode === 'user' ? 'environment' : 'user',
        }));
    }, []);

    // Restart camera when facing mode changes
    useEffect(() => {
        if (state.isActive) {
            stopCamera();
            startCamera();
        }
    }, [state.facingMode]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopCamera();
        };
    }, [stopCamera]);

    return {
        videoRef,
        state,
        startCamera,
        stopCamera,
        captureImage,
        switchCamera,
    };
}
