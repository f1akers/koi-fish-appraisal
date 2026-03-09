"""
Appraisal Schemas

Pydantic models for request/response validation.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class AppraisalRequest(BaseModel):
    """Request model for appraisal (used for JSON requests, not file uploads)."""

    image_base64: Optional[str] = Field(
        None,
        description="Base64 encoded image data",
    )


class PatternMetrics(BaseModel):
    """Pattern recognition metrics."""

    name: str = Field(..., description="Pattern name (ogon, sanke, kohaku)")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")


class AppraisalResponse(BaseModel):
    """Response model for appraisal results."""

    # Size metrics
    size_cm: float = Field(..., ge=0, description="Fish size in centimeters (median of N samples)")

    # Pattern metrics
    pattern_name: str = Field(..., description="Detected pattern name (majority vote)")
    pattern_confidence: float = Field(
        ..., ge=0, le=1, description="Mean confidence of winning pattern votes"
    )

    # Color proportions (dynamic named colors)
    color_proportions: Dict[str, float] = Field(
        ..., description="Named color to percentage mapping (values 0-100, sum ~100%)"
    )

    # Symmetry metrics
    symmetry_score: float = Field(..., ge=0, le=1, description="Bilateral symmetry score")

    class Config:
        json_schema_extra = {
            "example": {
                "size_cm": 25.4,
                "pattern_name": "kohaku",
                "pattern_confidence": 0.92,
                "color_proportions": {
                    "Red": 42.3,
                    "White": 35.1,
                    "Black": 22.6,
                },
                "symmetry_score": 0.87,
            }
        }
