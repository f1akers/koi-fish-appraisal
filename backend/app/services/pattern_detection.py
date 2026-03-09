"""
Pattern Recognition Service

Classifies koi fish patterns into predefined categories
(Ogon, Sanke, Kohaku) using a trained YOLO classification model.

Includes image augmentation and multi-sample aggregation utilities.
"""

import logging
from collections import Counter
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import numpy as np
from ultralytics import YOLO

from app.config import MODEL_PATHS, KOI_PATTERNS, DEFAULT_N_SAMPLES

logger = logging.getLogger(__name__)


class PatternDetector:
    """
    Detects and classifies koi fish pattern types using
    a trained YOLO classification model.
    """
    
    def __init__(self):
        """Initialize the pattern classification model."""
        self._model: Optional[YOLO] = None
    
    @property
    def model(self) -> YOLO:
        """Lazy load the pattern classification model."""
        if self._model is None:
            model_path = MODEL_PATHS["koi_pattern"]
            if not model_path.exists():
                raise FileNotFoundError(
                    f"Pattern classification model not found at {model_path}"
                )
            self._model = YOLO(str(model_path))
            logger.info(f"Loaded pattern classification model from {model_path}")
        return self._model
    
    def classify_pattern(
        self,
        image: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> Tuple[str, float]:
        """
        Classify the koi fish pattern.
        
        Args:
            image: Input image as numpy array (BGR format).
            mask: Optional segmentation mask to focus on fish region.
            
        Returns:
            Tuple of (pattern name, confidence score).
        """
        # If mask provided, extract fish region
        if mask is not None:
            fish_image = self._extract_fish_region(image, mask)
        else:
            fish_image = image
        
        # Run inference
        results = self.model(fish_image, verbose=False)
        
        if not results or len(results) == 0:
            logger.warning("No classification results")
            return "unknown", 0.0
        
        result = results[0]
        
        # Get class probabilities
        probs = result.probs
        if probs is None:
            logger.warning("No probability output from classifier")
            return "unknown", 0.0
        
        # Get top prediction
        top1_idx = int(probs.top1)
        top1_conf = float(probs.top1conf)
        
        # Get class name
        class_name = result.names[top1_idx]
        
        # Validate against known patterns
        if class_name.lower() not in [p.lower() for p in KOI_PATTERNS]:
            logger.warning(f"Unknown pattern class: {class_name}")
            class_name = "unknown"
        
        logger.info(f"Classified pattern: {class_name} (confidence: {top1_conf:.2%})")
        return class_name.lower(), top1_conf
    
    def _extract_fish_region(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """
        Extract the fish region from image using mask.
        
        Args:
            image: Input image.
            mask: Binary segmentation mask.
            
        Returns:
            Cropped image containing only the fish region.
        """
        # Find bounding box of mask
        coords = np.argwhere(mask > 0)
        if len(coords) == 0:
            return image
        
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        
        # Add padding
        padding = 10
        h, w = image.shape[:2]
        y_min = max(0, y_min - padding)
        x_min = max(0, x_min - padding)
        y_max = min(h, y_max + padding)
        x_max = min(w, x_max + padding)
        
        # Crop image
        cropped = image[y_min:y_max, x_min:x_max]
        
        # Apply mask to remove background
        mask_crop = mask[y_min:y_max, x_min:x_max]
        masked = cv2.bitwise_and(cropped, cropped, mask=mask_crop)
        
        return masked
    
    def get_all_probabilities(
        self,
        image: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> dict[str, float]:
        """
        Get probability scores for all pattern classes.
        
        Args:
            image: Input image as numpy array (BGR format).
            mask: Optional segmentation mask.
            
        Returns:
            Dictionary mapping pattern names to probabilities.
        """
        # If mask provided, extract fish region
        if mask is not None:
            fish_image = self._extract_fish_region(image, mask)
        else:
            fish_image = image
        
        # Run inference
        results = self.model(fish_image, verbose=False)
        
        if not results or len(results) == 0:
            return {pattern: 0.0 for pattern in KOI_PATTERNS}
        
        result = results[0]
        probs = result.probs
        
        if probs is None:
            return {pattern: 0.0 for pattern in KOI_PATTERNS}
        
        # Build probability dictionary
        prob_dict = {}
        for idx, prob in enumerate(probs.data.cpu().numpy()):
            class_name = result.names[idx].lower()
            prob_dict[class_name] = float(prob)
        
        return prob_dict


# Global instance for reuse
_pattern_detector: Optional[PatternDetector] = None


def get_pattern_detector() -> PatternDetector:
    """Get or create the global PatternDetector instance."""
    global _pattern_detector
    if _pattern_detector is None:
        _pattern_detector = PatternDetector()
    return _pattern_detector


def classify_koi_pattern(
    image: np.ndarray,
    mask: Optional[np.ndarray] = None
) -> Tuple[str, float]:
    """
    Convenience function to classify koi pattern.
    
    Args:
        image: Input image as numpy array (BGR format).
        mask: Optional segmentation mask.
        
    Returns:
        Tuple of (pattern name, confidence score).
    """
    detector = get_pattern_detector()
    return detector.classify_pattern(image, mask)


# =============================================================================
# Image Augmentation
# =============================================================================


def augment_image(image: np.ndarray, seed: int) -> np.ndarray:
    """
    Apply mild augmentation to an image for multi-sample inference.

    Augmentations: brightness/contrast jitter (+-10%), small rotation (+-5 deg),
    50% horizontal flip. seed=0 returns the original unaugmented image.

    Args:
        image: Input image (BGR numpy array).
        seed: Random seed. 0 returns the original image unmodified.

    Returns:
        Augmented (or original) image as numpy array.
    """
    if seed == 0:
        return image

    rng = np.random.default_rng(seed)

    # Brightness / contrast jitter
    alpha = rng.uniform(0.9, 1.1)   # contrast
    beta = rng.uniform(-10, 10)      # brightness
    augmented = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

    # Small rotation (+-5 degrees)
    angle = rng.uniform(-5, 5)
    h, w = augmented.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    augmented = cv2.warpAffine(augmented, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    # 50% horizontal flip
    if rng.random() > 0.5:
        augmented = cv2.flip(augmented, 1)

    return augmented


# =============================================================================
# Multi-Sample Pattern Aggregation
# =============================================================================


def classify_koi_pattern_multisample(
    image: np.ndarray,
    mask: Optional[np.ndarray] = None,
    n_samples: int = DEFAULT_N_SAMPLES,
) -> Tuple[str, float]:
    """
    Classify koi pattern using multiple augmented samples and majority vote.

    Generates *n_samples* augmented variants (seed 0 = original), runs pattern
    classification on each, then aggregates via majority vote for the pattern
    name and mean confidence of the winning votes. Ties are broken by highest
    mean confidence.

    Args:
        image: Input image (BGR numpy array).
        mask: Optional segmentation mask.
        n_samples: Number of inference samples (1 = single-pass, no augmentation).

    Returns:
        Tuple of (pattern_name, pattern_confidence).
    """
    if n_samples <= 1:
        return classify_koi_pattern(image, mask)

    detector = get_pattern_detector()
    results: List[Tuple[str, float]] = []

    for i in range(n_samples):
        aug_img = augment_image(image, seed=i)
        name, conf = detector.classify_pattern(aug_img, mask)
        results.append((name, conf))
        logger.debug(f"Sample {i}: pattern={name}, confidence={conf:.3f}")

    # Majority vote
    vote_counts = Counter(name for name, _ in results)
    max_votes = max(vote_counts.values())

    # Candidates tied at max votes
    tied = [name for name, cnt in vote_counts.items() if cnt == max_votes]

    # Break ties by highest mean confidence
    best_name = None
    best_mean_conf = -1.0
    for candidate in tied:
        confs = [conf for name, conf in results if name == candidate]
        mean_conf = float(np.mean(confs))
        if mean_conf > best_mean_conf:
            best_mean_conf = mean_conf
            best_name = candidate

    logger.info(
        f"Multi-sample pattern ({n_samples} runs): "
        f"{best_name} (confidence={best_mean_conf:.3f}, votes={vote_counts})"
    )
    return best_name, best_mean_conf
