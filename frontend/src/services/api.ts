/**
 * API Service
 *
 * Functions for communicating with the backend API.
 */

import type { AppraisalResult } from "../types";

// API base URL – set VITE_API_BASE_URL to backend's public URL for direct access,
// or use default "/api" for proxy (dev Vite proxy or production NGINX proxy)
const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

/**
 * Send an image for appraisal
 */
export async function appraiseImage(imageBlob: Blob): Promise<AppraisalResult> {
  const formData = new FormData();
  formData.append("image", imageBlob, "capture.jpg");

  const response = await fetch(`${API_BASE}/appraise`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to appraise image" }));
    throw new Error(error.detail || "Failed to appraise image");
  }

  return response.json();
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<{
  status: string;
  version: string;
}> {
  const response = await fetch(`${API_BASE}/health`);

  if (!response.ok) {
    throw new Error("API is not available");
  }

  return response.json();
}
