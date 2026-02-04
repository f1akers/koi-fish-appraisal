/**
 * TypeScript type definitions for Koi Fish Appraisal
 */

/**
 * Color metrics from analysis
 */
export interface ColorMetrics {
    white_pct: number;
    red_pct: number;
    black_pct: number;
    quality_score: number;
}

/**
 * Pattern recognition result
 */
export interface PatternMetrics {
    name: 'ogon' | 'showa' | 'kohaku' | 'unknown';
    confidence: number;
}

/**
 * Full appraisal result from API
 */
export interface AppraisalResult {
    size_cm: number;
    pattern_name: string;
    pattern_confidence: number;
    color_white_pct: number;
    color_red_pct: number;
    color_black_pct: number;
    color_quality_score: number;
    symmetry_score: number;
    predicted_price: number;
}

/**
 * Application state
 */
export interface AppState {
    capturedImage: Blob | null;
    imagePreview: string | null;
    appraisalResult: AppraisalResult | null;
    isLoading: boolean;
    error: string | null;
    history: AppraisalHistoryItem[];
}

/**
 * History item for batch export
 */
export interface AppraisalHistoryItem {
    id: string;
    timestamp: Date;
    imagePreview: string;
    result: AppraisalResult;
}

/**
 * Camera state
 */
export interface CameraState {
    isActive: boolean;
    hasPermission: boolean | null;
    facingMode: 'user' | 'environment';
    error: string | null;
}

/**
 * Training metrics response
 */
export interface TrainingMetrics {
    r2_score: number;
    mae: number;
    mse: number;
    rmse: number;
    samples_trained: number;
}

/**
 * API error response
 */
export interface ApiError {
    detail: string;
}
