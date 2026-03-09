"""
Appraisal Router

Endpoints for koi fish appraisal.
"""

import logging

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import DEFAULT_N_SAMPLES
from app.schemas.appraisal import AppraisalResponse
from app.services.size_detection import detect_fish_size_multisample
from app.services.pattern_detection import classify_koi_pattern_multisample
from app.services.color_analysis import analyze_fish_colors
from app.services.symmetry_analysis import analyze_fish_symmetry

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
    nparr = np.frombuffer(contents, np.uint8)
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
        AppraisalResponse containing size, pattern, color proportions, and symmetry.

    Raises:
        HTTPException: If image processing fails or required elements not detected.
    """
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image file.",
        )

    try:
        contents = await image.read()
        cv_image = _read_image_from_upload(contents)

        logger.info(f"Processing image: {image.filename}, size: {cv_image.shape}")

        # 1. Size detection with multi-sample aggregation (also returns representative mask)
        try:
            size_cm, mask, size_info = detect_fish_size_multisample(
                cv_image, n_samples=DEFAULT_N_SAMPLES
            )
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=f"Size detection failed: {str(e)}",
            )
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Model not available: {str(e)}",
            )

        # 2. Pattern recognition with multi-sample aggregation (majority vote)
        try:
            pattern_name, pattern_confidence = classify_koi_pattern_multisample(
                cv_image, mask, n_samples=DEFAULT_N_SAMPLES
            )
        except FileNotFoundError as e:
            logger.warning(f"Pattern model not available: {e}")
            pattern_name, pattern_confidence = "unknown", 0.0
        except Exception as e:
            logger.warning(f"Pattern detection failed: {e}")
            pattern_name, pattern_confidence = "unknown", 0.0

        # 3. Color analysis (K-Means in LAB colorspace)
        try:
            color_proportions = analyze_fish_colors(cv_image, mask)
        except Exception as e:
            logger.warning(f"Color analysis failed: {e}")
            color_proportions = {"Other": 100.0}

        # 4. Symmetry analysis
        try:
            symmetry_score = analyze_fish_symmetry(cv_image, mask)
        except Exception as e:
            logger.warning(f"Symmetry analysis failed: {e}")
            symmetry_score = 0.5

        return AppraisalResponse(
            size_cm=size_cm,
            pattern_name=pattern_name,
            pattern_confidence=pattern_confidence,
            color_proportions=color_proportions,
            symmetry_score=symmetry_score,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}",
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
            "path": str(path),
        }

    return {"models": status}

