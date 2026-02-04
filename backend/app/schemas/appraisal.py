"""
Appraisal Schemas

Pydantic models for request/response validation.
"""

from typing import Optional

from pydantic import BaseModel, Field


class AppraisalRequest(BaseModel):
    """Request model for appraisal (used for JSON requests, not file uploads)."""
    
    image_base64: Optional[str] = Field(
        None,
        description="Base64 encoded image data"
    )


class ColorMetrics(BaseModel):
    """Color analysis metrics."""
    
    white_pct: float = Field(..., ge=0, le=100, description="Percentage of white color")
    red_pct: float = Field(..., ge=0, le=100, description="Percentage of red color")
    black_pct: float = Field(..., ge=0, le=100, description="Percentage of black color")
    quality_score: float = Field(..., ge=0, le=1, description="Overall color quality score")


class PatternMetrics(BaseModel):
    """Pattern recognition metrics."""
    
    name: str = Field(..., description="Pattern name (ogon, showa, kohaku)")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")


class AppraisalResponse(BaseModel):
    """Response model for appraisal results."""
    
    # Size metrics
    size_cm: float = Field(..., ge=0, description="Fish size in centimeters")
    
    # Pattern metrics
    pattern_name: str = Field(..., description="Detected pattern name")
    pattern_confidence: float = Field(..., ge=0, le=1, description="Pattern detection confidence")
    
    # Color metrics
    color_white_pct: float = Field(..., ge=0, le=100, description="Percentage of white")
    color_red_pct: float = Field(..., ge=0, le=100, description="Percentage of red")
    color_black_pct: float = Field(..., ge=0, le=100, description="Percentage of black")
    color_quality_score: float = Field(..., ge=0, le=1, description="Color quality score")
    
    # Symmetry metrics
    symmetry_score: float = Field(..., ge=0, le=1, description="Bilateral symmetry score")
    
    # Price prediction
    predicted_price: float = Field(..., ge=0, description="Predicted price")
    
    class Config:
        json_schema_extra = {
            "example": {
                "size_cm": 25.4,
                "pattern_name": "kohaku",
                "pattern_confidence": 0.95,
                "color_white_pct": 45.2,
                "color_red_pct": 38.1,
                "color_black_pct": 16.7,
                "color_quality_score": 0.85,
                "symmetry_score": 0.87,
                "predicted_price": 85000.0,
            }
        }


class TrainingMetrics(BaseModel):
    """Metrics from model training."""
    
    r2_score: float = Field(..., description="R-squared score")
    mae: float = Field(..., description="Mean Absolute Error")
    mse: float = Field(..., description="Mean Squared Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    samples_trained: int = Field(..., description="Number of training samples")


class TrainingResponse(BaseModel):
    """Response model for training endpoint."""
    
    status: str = Field(..., description="Training status")
    metrics: Optional[TrainingMetrics] = Field(None, description="Training metrics if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
