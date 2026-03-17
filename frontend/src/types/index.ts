/**
 * TypeScript type definitions for Koi Fish Appraisal
 */

/**
 * Pattern recognition result
 */
export interface PatternMetrics {
  name: "ogon" | "sanke" | "kohaku" | "unknown";
  confidence: number;
}

/**
 * Full appraisal result from API
 */
export interface AppraisalResult {
  size_cm: number;
  pattern_name: string;
  pattern_confidence: number;
  color_proportions: Record<string, number>;
  symmetry_score: number;
  color_score: number;
  overall_score: number;
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
  facingMode: "user" | "environment";
  error: string | null;
}

/**
 * API error response
 */
export interface ApiError {
  detail: string;
}
