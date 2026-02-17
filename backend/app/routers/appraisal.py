"""
Appraisal Router

Endpoints for koi fish appraisal.
"""

import io
import logging
from typing import Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.config import KOI_PATTERNS
from app.schemas.appraisal import (
    AppraisalResponse,
    TrainingRequest,
    TrainingResponse,
    PatternTrainingMetrics,
)
from app.services.size_detection import detect_fish_size
from app.services.pattern_detection import classify_koi_pattern
from app.services.color_analysis import analyze_fish_colors
from app.services.symmetry_analysis import analyze_fish_symmetry
from app.services.price_prediction import get_price_predictor

logger = logging.getLogger(__name__)

router = APIRouter()


def _read_image_from_upload(contents: bytes) -> np.ndarray:
    """
    Convert uploaded file contents to OpenCV image.
    
    Args:
        contents: Raw bytes from uploaded file.
        
    Returns:
        Image as numpy array in BGR format.
        
    Raises:
        ValueError: If image cannot be decoded.
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(contents, np.uint8)
    
    # Decode image
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Could not decode image")
    
    return image


@router.post("/appraise", response_model=AppraisalResponse)
async def appraise_koi(image: UploadFile = File(...)) -> AppraisalResponse:
    """
    Appraise a koi fish from an uploaded image.
    
    The image should contain:
    - A koi fish clearly visible
    - A reference coin (Philippine Peso) for size calculation
    
    Returns:
        AppraisalResponse containing all metrics and predicted price.
        
    Raises:
        HTTPException: If image processing fails or required elements not detected.
    """
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image file."
        )
    
    try:
        # Read image bytes
        contents = await image.read()
        
        # Convert to OpenCV image
        cv_image = _read_image_from_upload(contents)
        
        logger.info(f"Processing image: {image.filename}, size: {cv_image.shape}")
        
        # 1. Size detection (also returns segmentation mask)
        try:
            size_cm, mask, size_info = detect_fish_size(cv_image)
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=f"Size detection failed: {str(e)}"
            )
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Model not available: {str(e)}"
            )
        
        # 2. Pattern recognition
        try:
            pattern_name, pattern_confidence = classify_koi_pattern(cv_image, mask)
        except FileNotFoundError as e:
            logger.warning(f"Pattern model not available: {e}")
            pattern_name, pattern_confidence = "unknown", 0.0
        except Exception as e:
            logger.warning(f"Pattern detection failed: {e}")
            pattern_name, pattern_confidence = "unknown", 0.0
        
        # 3. Color analysis
        try:
            color_metrics = analyze_fish_colors(cv_image, mask)
        except Exception as e:
            logger.warning(f"Color analysis failed: {e}")
            color_metrics = {
                "white_pct": 0.0,
                "red_pct": 0.0,
                "black_pct": 0.0,
                "quality_score": 0.0
            }
        
        # 4. Symmetry analysis
        try:
            symmetry_score = analyze_fish_symmetry(cv_image, mask)
        except Exception as e:
            logger.warning(f"Symmetry analysis failed: {e}")
            symmetry_score = 0.5
        
        # 5. Price prediction (uses per-pattern model)
        predicted_price = 0.0
        predictor = get_price_predictor()
        
        if pattern_name not in KOI_PATTERNS:
            logger.info(
                f"Pattern '{pattern_name}' is not a known type — "
                "skipping price prediction"
            )
        elif predictor.is_model_available(pattern_name):
            try:
                predicted_price = predictor.predict(
                    pattern_name=pattern_name,
                    pattern_confidence=pattern_confidence,
                    color_white_pct=color_metrics["white_pct"],
                    color_red_pct=color_metrics["red_pct"],
                    color_black_pct=color_metrics["black_pct"],
                    color_quality_score=color_metrics["quality_score"],
                    symmetry_score=symmetry_score
                )
            except Exception as e:
                logger.warning(f"Price prediction failed: {e}")
                predicted_price = 0.0
        else:
            logger.info(
                f"Price prediction model for '{pattern_name}' not trained yet"
            )
        
        return AppraisalResponse(
            size_cm=size_cm,
            pattern_name=pattern_name,
            pattern_confidence=pattern_confidence,
            color_white_pct=color_metrics["white_pct"],
            color_red_pct=color_metrics["red_pct"],
            color_black_pct=color_metrics["black_pct"],
            color_quality_score=color_metrics["quality_score"],
            symmetry_score=symmetry_score,
            predicted_price=predicted_price,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


@router.post("/train", response_model=TrainingResponse)
async def trigger_training(body: TrainingRequest) -> TrainingResponse:
    """
    Trigger per-pattern training of linear regression models.

    Accepts a JSON body with ``ogon``, ``sanke``, and ``kohaku``
    configs, each containing ``csv_path`` and ``images_dir``.

    Returns:
        Training status and per-pattern metrics.
    """
    try:
        # Import trainer here to avoid circular imports
        from app.train import train_all_patterns

        pattern_configs = {}
        for name, cfg in [
            ("ogon", body.ogon),
            ("sanke", body.sanke),
            ("kohaku", body.kohaku),
        ]:
            if cfg is not None:
                pattern_configs[name] = {
                    "csv_path": cfg.csv_path,
                    "images_dir": cfg.images_dir,
                }

        if not pattern_configs:
            return TrainingResponse(
                status="error",
                pattern_metrics=None,
                error="At least one pattern config must be provided.",
            )

        logger.info(
            f"Starting per-pattern training for: "
            f"{list(pattern_configs.keys())}"
        )

        all_metrics = train_all_patterns(pattern_configs)

        pattern_metrics = {
            pattern: PatternTrainingMetrics(
                r2_score=m["r2_score"],
                mae=m["mae"],
                mse=m["mse"],
                rmse=m["rmse"],
                samples_trained=m["samples_trained"],
            )
            for pattern, m in all_metrics.items()
        }

        return TrainingResponse(
            status="success",
            pattern_metrics=pattern_metrics,
            error=None,
        )

    except FileNotFoundError as e:
        logger.error(f"Training file not found: {e}")
        return TrainingResponse(
            status="error",
            pattern_metrics=None,
            error=f"File not found: {str(e)}",
        )
    except ValueError as e:
        logger.error(f"Training validation error: {e}")
        return TrainingResponse(
            status="error",
            pattern_metrics=None,
            error=str(e),
        )
    except Exception as e:
        logger.exception(f"Training failed: {e}")
        return TrainingResponse(
            status="error",
            pattern_metrics=None,
            error=f"Training failed: {str(e)}",
        )


@router.get("/model-status")
async def get_model_status() -> dict:
    """
    Check the status of ML models.
    
    Returns:
        Dictionary with model availability status.
    """
    from app.config import MODEL_PATHS
    
    status = {}
    
    for name, path in MODEL_PATHS.items():
        status[name] = {
            "available": path.exists(),
            "path": str(path)
        }
    
    return {"models": status}

