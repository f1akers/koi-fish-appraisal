"""
Feature Extraction Utilities

Builds the feature vector consumed by the expert-scoring XGBoost models.
Used by both the training pipeline (app/train.py) and the serving service
(app/services/expert_scoring.py) so training and production features
always match.

Features are extracted from the coin-free part of the appraisal pipeline
(segmentation mask -> symmetry, colors, pattern). Fish size is intentionally
excluded: training images do not contain a reference coin.
"""

import logging

import cv2

from app.config import DEFAULT_N_SAMPLES, KOI_PATTERNS
from app.services.color_analysis import analyze_fish_colors
from app.services.color_scoring import score_fish_colors
from app.services.pattern_detection import classify_koi_pattern_multisample
from app.services.size_detection import detect_fish_mask
from app.services.symmetry_analysis import analyze_fish_symmetry

logger = logging.getLogger(__name__)

# Canonical feature columns shared by training and serving.
# Order matters: must stay identical between app/train.py and
# app/services/expert_scoring.py.
FEATURE_COLUMNS: list[str] = [
    "pattern_ogon",
    "pattern_sanke",
    "pattern_kohaku",
    "pattern_confidence",
    "symmetry_score",
    "color_score",
    "color_White",
    "color_Red",
    "color_Black",
    "color_Orange",
    "color_Yellow",
]

# Named colors kept as features (must match KOI_COLOR_MAP keys).
_COLOR_FEATURES: list[str] = ["White", "Red", "Black", "Orange", "Yellow"]


def build_feature_vector(
    pattern_name: str,
    pattern_confidence: float,
    symmetry_score: float,
    color_proportions: dict[str, float],
) -> dict[str, float]:
    """
    Assemble the canonical feature vector from pipeline outputs.

    Args:
        pattern_name: Detected pattern ('ogon', 'sanke', 'kohaku', or 'unknown').
        pattern_confidence: Classification confidence (0-1).
        symmetry_score: Bilateral symmetry score (0-1).
        color_proportions: Named color to percentage mapping from color analysis.

    Returns:
        Dictionary with exactly the keys in FEATURE_COLUMNS.
    """
    one_hot = {
        f"pattern_{pattern}": 1.0 if pattern_name == pattern else 0.0
        for pattern in KOI_PATTERNS
    }

    features: dict[str, float] = {}
    features.update(one_hot)
    features["pattern_confidence"] = float(pattern_confidence)
    features["symmetry_score"] = float(symmetry_score)
    features["color_score"] = float(score_fish_colors(pattern_name, color_proportions))
    for color in _COLOR_FEATURES:
        features[f"color_{color}"] = float(color_proportions.get(color, 0.0))
    return features


def extract_appraisal_features(image_path: str) -> dict[str, float] | None:
    """
    Extract the expert-scoring feature vector from a single image file.

    Runs the coin-free pipeline: segmentation mask -> symmetry, colors,
    and multi-sample pattern classification. Mirrors the production
    feature assembly (app/routers/appraisal.py).

    Args:
        image_path: Path to the image file.

    Returns:
        Feature dictionary (FEATURE_COLUMNS keys), or None if the fish
        could not be segmented or a pipeline stage failed.
    """
    image = cv2.imread(image_path)
    if image is None:
        logger.warning(f"Could not read image: {image_path}")
        return None

    mask, _ = detect_fish_mask(image)
    if mask is None:
        logger.warning(f"No fish detected in: {image_path}")
        return None

    try:
        symmetry_score = analyze_fish_symmetry(image, mask)
        color_proportions = analyze_fish_colors(image, mask)
        pattern_name, pattern_confidence = classify_koi_pattern_multisample(
            image, mask, n_samples=DEFAULT_N_SAMPLES
        )
    except Exception as e:
        logger.warning(f"Pipeline failed for {image_path}: {e}")
        return None

    return build_feature_vector(
        pattern_name=pattern_name,
        pattern_confidence=pattern_confidence,
        symmetry_score=symmetry_score,
        color_proportions=color_proportions,
    )
