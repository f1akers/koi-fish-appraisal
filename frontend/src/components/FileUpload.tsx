/**
 * FileUpload Component
 *
 * Drag-and-drop or click-to-browse file upload for koi fish images.
 * Flat design with gradient accents matching the app theme.
 */

import { useState, useRef, useCallback } from 'react';

interface FileUploadProps {
    onUpload: (imageBlob: Blob) => void;
    isProcessing: boolean;
}

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20 MB

export function FileUpload({ onUpload, isProcessing }: FileUploadProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [preview, setPreview] = useState<string | null>(null);
    const [fileName, setFileName] = useState<string | null>(null);
    const [validationError, setValidationError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const pendingBlobRef = useRef<Blob | null>(null);

    const validateFile = (file: File): string | null => {
        if (!ACCEPTED_TYPES.includes(file.type)) {
            return 'Please upload a JPEG, PNG, or WebP image.';
        }
        if (file.size > MAX_FILE_SIZE) {
            return 'File size must be under 20 MB.';
        }
        return null;
    };

    const handleFile = useCallback((file: File) => {
        setValidationError(null);

        const error = validateFile(file);
        if (error) {
            setValidationError(error);
            return;
        }

        // Show preview
        const url = URL.createObjectURL(file);
        if (preview) URL.revokeObjectURL(preview);
        setPreview(url);
        setFileName(file.name);
        pendingBlobRef.current = file;
    }, [preview]);

    const handleSubmit = useCallback(() => {
        if (pendingBlobRef.current) {
            onUpload(pendingBlobRef.current);
        }
    }, [onUpload]);

    const handleClear = useCallback(() => {
        if (preview) URL.revokeObjectURL(preview);
        setPreview(null);
        setFileName(null);
        setValidationError(null);
        pendingBlobRef.current = null;
        if (fileInputRef.current) fileInputRef.current.value = '';
    }, [preview]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    }, [handleFile]);

    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleFile(file);
    }, [handleFile]);

    return (
        <div className="relative w-full max-w-2xl mx-auto">
            {/* Drop zone / preview */}
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !preview && !isProcessing && fileInputRef.current?.click()}
                className={`relative aspect-[4/3] rounded-3xl overflow-hidden transition-all duration-200 ${preview
                        ? 'bg-gray-900'
                        : isDragging
                            ? 'bg-violet-50 border-2 border-dashed border-violet-400 cursor-pointer'
                            : 'bg-gradient-to-br from-gray-50 to-gray-100 border-2 border-dashed border-gray-300 hover:border-violet-400 hover:from-violet-50 hover:to-purple-50 cursor-pointer'
                    }`}
            >
                {/* Preview image */}
                {preview ? (
                    <>
                        <img
                            src={preview}
                            alt="Koi preview"
                            className="w-full h-full object-contain"
                        />

                        {/* Processing overlay */}
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
                    </>
                ) : (
                    /* Upload prompt */
                    <div className="absolute inset-0 flex flex-col items-center justify-center p-8">
                        <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-colors duration-200 ${isDragging
                                ? 'bg-gradient-to-br from-violet-400 to-purple-500'
                                : 'bg-gradient-to-br from-gray-200 to-gray-300'
                            }`}>
                            <svg className={`w-10 h-10 ${isDragging ? 'text-white' : 'text-gray-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <p className="text-lg font-semibold text-gray-800 mb-1">
                            {isDragging ? 'Drop your image here' : 'Upload a koi photo'}
                        </p>
                        <p className="text-gray-500 text-sm text-center">
                            Drag & drop or <span className="text-violet-600 font-medium">browse</span> to choose a file
                        </p>
                        <p className="text-gray-400 text-xs mt-2">JPEG, PNG, or WebP · Max 20 MB</p>
                    </div>
                )}
            </div>

            {/* Hidden file input */}
            <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_TYPES.join(',')}
                onChange={handleInputChange}
                className="hidden"
            />

            {/* Validation error */}
            {validationError && (
                <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600 text-center">
                    {validationError}
                </div>
            )}

            {/* Action buttons */}
            <div className="mt-6 flex flex-col items-center gap-4">
                {preview ? (
                    <div className="flex items-center gap-4">
                        {/* Clear button */}
                        <button
                            onClick={handleClear}
                            disabled={isProcessing}
                            className="w-14 h-14 rounded-2xl bg-gray-100 hover:bg-gray-200 transition-all duration-200 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                            aria-label="Remove image"
                        >
                            <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </button>

                        {/* Submit button */}
                        <button
                            onClick={handleSubmit}
                            disabled={isProcessing}
                            className="w-20 h-20 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 transition-all duration-200 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
                            aria-label="Appraise image"
                        >
                            <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center">
                                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                            </div>
                        </button>

                        {/* Change file button */}
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            disabled={isProcessing}
                            className="w-14 h-14 rounded-2xl bg-gray-100 hover:bg-gray-200 transition-all duration-200 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                            aria-label="Choose different image"
                        >
                            <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                        </button>
                    </div>
                ) : (
                    /* Browse button when no preview */
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isProcessing}
                        className="px-6 py-3 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
                    >
                        Choose Photo
                    </button>
                )}

                {/* Status text */}
                <p className="text-gray-500 text-sm">
                    {isProcessing
                        ? 'Processing...'
                        : preview
                            ? fileName ?? 'Image selected'
                            : 'Select a koi fish photo to appraise'}
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
                            Use a well-lit photo where both the koi fish and reference coin are fully visible. Top-down shots work best.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
