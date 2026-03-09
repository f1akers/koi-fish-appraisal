"""
Size Detection Service

Calculates the actual size of koi fish in centimeters using
instance segmentation and reference coin detection.

Includes multi-sample aggregation for robust size measurement.
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import numpy as np
from ultralytics import YOLO

from app.config import MODEL_PATHS, get_coin_diameter_cm, DEFAULT_N_SAMPLES

logger = logging.getLogger(__name__)


class SizeDetector:
    """
    Detects and calculates koi fish size using segmentation
    and a reference coin for scale calibration.
    """
    
    def __init__(self):
        """Initialize models for size detection."""
        self._koi_segment_model: Optional[YOLO] = None
        self._coin_detect_model: Optional[YOLO] = None
    
    @property
    def koi_segment_model(self) -> YOLO:
        """Lazy load the koi segmentation model."""
        if self._koi_segment_model is None:
            model_path = MODEL_PATHS["koi_segment"]
            if not model_path.exists():
                raise FileNotFoundError(
                    f"Koi segmentation model not found at {model_path}"
                )
            self._koi_segment_model = YOLO(str(model_path))
            logger.info(f"Loaded koi segmentation model from {model_path}")
        return self._koi_segment_model
    
    @property
    def coin_detect_model(self) -> YOLO:
        """Lazy load the coin detection model."""
        if self._coin_detect_model is None:
            model_path = MODEL_PATHS["coin_detect"]
            if not model_path.exists():
                raise FileNotFoundError(
                    f"Coin detection model not found at {model_path}"
                )
            self._coin_detect_model = YOLO(str(model_path))
            logger.info(f"Loaded coin detection model from {model_path}")
        return self._coin_detect_model
    
    def detect_fish_mask(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], int]:
        """
        Detect koi fish and return segmentation mask.
        
        Args:
            image: Input image as numpy array (BGR format).
            
        Returns:
            Tuple of (segmentation mask as binary numpy array, pixel count).
            Returns (None, 0) if no fish detected.
        """
        results = self.koi_segment_model(image, verbose=False)
        
        if not results or len(results) == 0:
            logger.warning("No detection results from segmentation model")
            return None, 0
        
        result = results[0]
        
        if result.masks is None or len(result.masks) == 0:
            logger.warning("No segmentation masks found")
            return None, 0
        
        # Get the first (most confident) mask
        # Masks are in normalized format, need to resize to image dimensions
        mask = result.masks[0].data.cpu().numpy().squeeze()
        
        # Resize mask to match image dimensions
        h, w = image.shape[:2]
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
        
        # Convert to binary mask
        binary_mask = (mask > 0.5).astype(np.uint8)
        
        # Count pixels
        pixel_count = np.sum(binary_mask)
        
        logger.info(f"Detected fish with {pixel_count} pixels")
        return binary_mask, int(pixel_count)
    
    def detect_coin(self, image: np.ndarray) -> Tuple[Optional[str], Optional[np.ndarray], int]:
        """
        Detect reference coin and return its class and bounding box.
        
        Args:
            image: Input image as numpy array (BGR format).
            
        Returns:
            Tuple of (coin class name, bounding box [x1,y1,x2,y2], pixel count).
            Returns (None, None, 0) if no coin detected.
        """
        results = self.coin_detect_model(image, verbose=False)
        
        if not results or len(results) == 0:
            logger.warning("No detection results from coin model")
            return None, None, 0
        
        result = results[0]
        
        if result.boxes is None or len(result.boxes) == 0:
            logger.warning("No coin detected in image")
            return None, None, 0
        
        # Get the most confident detection
        boxes = result.boxes
        confidences = boxes.conf.cpu().numpy()
        best_idx = np.argmax(confidences)
        
        # Get class name
        class_id = int(boxes.cls[best_idx].cpu().numpy())
        class_name = result.names[class_id]
        
        # Get bounding box
        bbox = boxes.xyxy[best_idx].cpu().numpy()
        
        # Calculate coin pixel diameter (using the average of width and height)
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        # Use the larger dimension as diameter (coins should be roughly circular)
        diameter_pixels = max(width, height)
        
        # Approximate pixel area for a circle
        pixel_count = int(np.pi * (diameter_pixels / 2) ** 2)
        
        logger.info(f"Detected coin: {class_name} with diameter {diameter_pixels:.1f} pixels")
        return class_name, bbox, int(diameter_pixels)
    
    def calculate_ppc(self, coin_class: str, coin_diameter_pixels: int) -> float:
        """
        Calculate Pixels Per Centimeter (PPC).
        
        Args:
            coin_class: Detected coin class name.
            coin_diameter_pixels: Coin diameter in pixels.
            
        Returns:
            Pixels per centimeter value.
        """
        coin_diameter_cm = get_coin_diameter_cm(coin_class)
        ppc = coin_diameter_pixels / coin_diameter_cm
        logger.info(f"Calculated PPC: {ppc:.2f} (coin: {coin_class}, {coin_diameter_cm}cm)")
        return ppc
    
    def calculate_fish_size(
        self,
        fish_pixel_count: int,
        ppc: float
    ) -> float:
        """
        Calculate fish size in centimeters.
        
        Uses the pixel count and PPC to estimate the fish's area,
        then converts to an equivalent "size" metric (approximating length).
        
        Args:
            fish_pixel_count: Number of pixels in fish mask.
            ppc: Pixels per centimeter.
            
        Returns:
            Estimated fish size in centimeters.
        """
        # Convert pixel count to square centimeters
        area_cm2 = fish_pixel_count / (ppc ** 2)
        
        # Koi fish have roughly a 5:1 to 6:1 length to width ratio
        # Approximate the fish as an ellipse: Area = π * a * b
        # Where a is half-length and b is half-width
        # If L = 5.5 * W, then Area = π * (L/2) * (L/11) = π * L² / 22
        # So L = sqrt(22 * Area / π)
        aspect_ratio = 5.5  # Length to width ratio
        estimated_length_cm = np.sqrt(
            (4 * aspect_ratio * area_cm2) / np.pi
        )
        
        logger.info(f"Calculated fish size: {estimated_length_cm:.2f} cm")
        return float(estimated_length_cm)
    
    def detect_size(self, image: np.ndarray) -> Tuple[float, np.ndarray, dict]:
        """
        Main method to detect fish size from an image.
        
        Args:
            image: Input image as numpy array (BGR format).
            
        Returns:
            Tuple of:
                - Fish size in centimeters
                - Segmentation mask
                - Additional info dict (coin class, ppc, etc.)
                
        Raises:
            ValueError: If fish or coin not detected.
        """
        # Detect fish mask
        fish_mask, fish_pixels = self.detect_fish_mask(image)
        if fish_mask is None:
            raise ValueError("Could not detect koi fish in image")
        
        # Detect coin
        coin_class, coin_bbox, coin_diameter_px = self.detect_coin(image)
        if coin_class is None:
            raise ValueError("Could not detect reference coin in image")
        
        # Calculate PPC
        ppc = self.calculate_ppc(coin_class, coin_diameter_px)
        
        # Calculate fish size
        size_cm = self.calculate_fish_size(fish_pixels, ppc)
        
        info = {
            "coin_class": coin_class,
            "coin_diameter_pixels": coin_diameter_px,
            "fish_pixel_count": fish_pixels,
            "ppc": ppc,
        }
        
        return size_cm, fish_mask, info


# Global instance for reuse
_size_detector: Optional[SizeDetector] = None


def get_size_detector() -> SizeDetector:
    """Get or create the global SizeDetector instance."""
    global _size_detector
    if _size_detector is None:
        _size_detector = SizeDetector()
    return _size_detector


def detect_fish_size(image: np.ndarray) -> Tuple[float, np.ndarray, dict]:
    """
    Convenience function to detect fish size.
    
    Args:
        image: Input image as numpy array (BGR format).
        
    Returns:
        Tuple of (size in cm, segmentation mask, info dict).
    """
    detector = get_size_detector()
    return detector.detect_size(image)


def detect_fish_mask(image: np.ndarray) -> Tuple[Optional[np.ndarray], int]:
    """
    Convenience function to detect fish segmentation mask only.
    
    Does NOT require a reference coin in the image.
    
    Args:
        image: Input image as numpy array (BGR format).
        
    Returns:
        Tuple of (binary segmentation mask, pixel count).
        Returns (None, 0) if no fish detected.
    """
    detector = get_size_detector()
    return detector.detect_fish_mask(image)


# =============================================================================
# Multi-Sample Size Aggregation
# =============================================================================


def detect_fish_size_multisample(
    image: np.ndarray,
    n_samples: int = DEFAULT_N_SAMPLES,
) -> Tuple[float, np.ndarray, dict]:
    """
    Detect fish size using multiple augmented samples and median aggregation.

    Coin detection runs once (coins don't benefit from augmentation).
    Segmentation runs on each augmented variant. The final size is the median
    of all size measurements, and the representative mask is from the run
    closest to the median.

    Args:
        image: Input image (BGR numpy array).
        n_samples: Number of inference samples (1 = single-pass).

    Returns:
        Tuple of (size_cm, representative_mask, info_dict).

    Raises:
        ValueError: If fish or coin not detected.
    """
    if n_samples <= 1:
        return detect_fish_size(image)

    from app.services.pattern_detection import augment_image

    detector = get_size_detector()

    # Coin detection runs once on the original image
    coin_class, coin_bbox, coin_diameter_px = detector.detect_coin(image)
    if coin_class is None:
        raise ValueError("Could not detect reference coin in image")
    ppc = detector.calculate_ppc(coin_class, coin_diameter_px)

    # Run segmentation on each augmented variant
    sizes: List[float] = []
    masks: List[np.ndarray] = []

    for i in range(n_samples):
        aug_img = augment_image(image, seed=i)
        fish_mask, fish_pixels = detector.detect_fish_mask(aug_img)
        if fish_mask is None:
            logger.warning(f"Sample {i}: no fish detected, skipping")
            continue
        size_cm = detector.calculate_fish_size(int(fish_pixels), ppc)
        sizes.append(size_cm)
        masks.append(fish_mask)
        logger.debug(f"Sample {i}: size={size_cm:.2f} cm")

    if len(sizes) == 0:
        raise ValueError("Could not detect koi fish in any sample")

    # Aggregate via median
    median_size = float(np.median(sizes))

    # Select representative mask (closest to median)
    diffs = [abs(s - median_size) for s in sizes]
    best_idx = int(np.argmin(diffs))
    representative_mask = masks[best_idx]

    info = {
        "coin_class": coin_class,
        "coin_diameter_pixels": coin_diameter_px,
        "ppc": ppc,
        "n_samples": n_samples,
        "n_successful": len(sizes),
        "all_sizes": sizes,
        "median_size": median_size,
        "selected_sample": best_idx,
    }

    logger.info(
        f"Multi-sample size ({len(sizes)}/{n_samples} runs): "
        f"median={median_size:.2f} cm, sizes={[round(s, 2) for s in sizes]}"
    )
    return median_size, representative_mask, info
