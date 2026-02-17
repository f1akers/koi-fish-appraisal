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
    name: 'ogon' | 'sanke' | 'kohaku' | 'unknown';
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
 * Per-pattern training metrics
 */
export interface PatternTrainingMetrics {
    r2_score: number;
    mae: number;
    mse: number;
    rmse: number;
    samples_trained: number;
}

/**
 * Training response with per-pattern metrics
 */
export interface TrainingResponse {
    status: string;
    pattern_metrics: Record<string, PatternTrainingMetrics> | null;
    error: string | null;
}

/**
 * Training request config for a single pattern
 */
export interface PatternTrainingConfig {
    csv_path: string;
    images_dir: string;
}

/**
 * Training request body (per-pattern)
 */
export interface TrainingRequest {
    ogon?: PatternTrainingConfig;
    sanke?: PatternTrainingConfig;
    kohaku?: PatternTrainingConfig;
}

/**
 * API error response
 */
export interface ApiError {
    detail: string;
}
