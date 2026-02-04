"""
Color Analysis Service

Quantifies color distribution and quality of koi fish patterns
using HSV color space analysis with configurable thresholds.

Supports calibration through a separate calibration UI.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# Default calibration file path
CALIBRATION_FILE = settings.MODEL_PATH / "color_calibration.json"


# =============================================================================
# Default Color Thresholds (HSV)
# =============================================================================
# These are starting values that can be adjusted through calibration
# HSV ranges in OpenCV: H (0-179), S (0-255), V (0-255)
# =============================================================================

DEFAULT_COLOR_THRESHOLDS = {
    "white": {
        "lower": [0, 0, 180],      # Low saturation, high value
        "upper": [179, 50, 255],
        "description": "White (shiroji) areas"
    },
    "red": {
        # Red wraps around in HSV, so we need two ranges
        "lower1": [0, 100, 100],    # Lower red range
        "upper1": [10, 255, 255],
        "lower2": [160, 100, 100],  # Upper red range (wraps)
        "upper2": [179, 255, 255],
        "description": "Red/Orange (hi) areas"
    },
    "black": {
        "lower": [0, 0, 0],         # Very dark areas
        "upper": [179, 255, 50],
        "description": "Black (sumi) areas"
    },
}


class ColorAnalyzer:
    """
    Analyzes color distribution and quality in koi fish images.
    
    Uses HSV color space with configurable thresholds that can
    be calibrated for different lighting conditions.
    """
    
    def __init__(self, calibration_path: Optional[Path] = None):
        """
        Initialize the color analyzer.
        
        Args:
            calibration_path: Path to calibration file. If None, uses default.
        """
        self.calibration_path = calibration_path or CALIBRATION_FILE
        self.thresholds = self._load_thresholds()
    
    def _load_thresholds(self) -> dict:
        """Load calibration thresholds from file or use defaults."""
        if self.calibration_path.exists():
            try:
                with open(self.calibration_path, 'r') as f:
                    thresholds = json.load(f)
                logger.info(f"Loaded color calibration from {self.calibration_path}")
                return thresholds
            except Exception as e:
                logger.warning(f"Failed to load calibration: {e}. Using defaults.")
        
        return DEFAULT_COLOR_THRESHOLDS.copy()
    
    def save_thresholds(self, thresholds: dict) -> None:
        """
        Save calibration thresholds to file.
        
        Args:
            thresholds: Dictionary of color thresholds.
        """
        self.calibration_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.calibration_path, 'w') as f:
            json.dump(thresholds, f, indent=2)
        self.thresholds = thresholds
        logger.info(f"Saved color calibration to {self.calibration_path}")
    
    def analyze_colors(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> Dict[str, float]:
        """
        Analyze color distribution within the fish region.
        
        Args:
            image: Input image as numpy array (BGR format).
            mask: Binary segmentation mask.
            
        Returns:
            Dictionary containing:
                - white_pct: Percentage of white
                - red_pct: Percentage of red
                - black_pct: Percentage of black
                - quality_score: Overall color quality (0-1)
        """
        # Apply mask to extract fish region
        fish_region = cv2.bitwise_and(image, image, mask=mask)
        
        # Convert to HSV
        hsv = cv2.cvtColor(fish_region, cv2.COLOR_BGR2HSV)
        
        # Count total fish pixels
        total_pixels = np.sum(mask > 0)
        if total_pixels == 0:
            return {
                "white_pct": 0.0,
                "red_pct": 0.0,
                "black_pct": 0.0,
                "quality_score": 0.0
            }
        
        # Create color masks
        white_mask = self._create_white_mask(hsv, mask)
        red_mask = self._create_red_mask(hsv, mask)
        black_mask = self._create_black_mask(hsv, mask)
        
        # Calculate percentages
        white_pct = (np.sum(white_mask > 0) / total_pixels) * 100
        red_pct = (np.sum(red_mask > 0) / total_pixels) * 100
        black_pct = (np.sum(black_mask > 0) / total_pixels) * 100
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            hsv, mask, white_mask, red_mask, black_mask
        )
        
        logger.info(
            f"Color analysis: white={white_pct:.1f}%, red={red_pct:.1f}%, "
            f"black={black_pct:.1f}%, quality={quality_score:.2f}"
        )
        
        return {
            "white_pct": float(white_pct),
            "red_pct": float(red_pct),
            "black_pct": float(black_pct),
            "quality_score": float(quality_score)
        }
    
    def _create_white_mask(
        self,
        hsv: np.ndarray,
        fish_mask: np.ndarray
    ) -> np.ndarray:
        """Create mask for white areas."""
        thresh = self.thresholds["white"]
        lower = np.array(thresh["lower"])
        upper = np.array(thresh["upper"])
        color_mask = cv2.inRange(hsv, lower, upper)
        return cv2.bitwise_and(color_mask, color_mask, mask=fish_mask)
    
    def _create_red_mask(
        self,
        hsv: np.ndarray,
        fish_mask: np.ndarray
    ) -> np.ndarray:
        """Create mask for red areas (handles HSV wrap-around)."""
        thresh = self.thresholds["red"]
        
        # Lower red range
        lower1 = np.array(thresh["lower1"])
        upper1 = np.array(thresh["upper1"])
        mask1 = cv2.inRange(hsv, lower1, upper1)
        
        # Upper red range (wrap-around)
        lower2 = np.array(thresh["lower2"])
        upper2 = np.array(thresh["upper2"])
        mask2 = cv2.inRange(hsv, lower2, upper2)
        
        # Combine both ranges
        red_mask = cv2.bitwise_or(mask1, mask2)
        return cv2.bitwise_and(red_mask, red_mask, mask=fish_mask)
    
    def _create_black_mask(
        self,
        hsv: np.ndarray,
        fish_mask: np.ndarray
    ) -> np.ndarray:
        """Create mask for black areas."""
        thresh = self.thresholds["black"]
        lower = np.array(thresh["lower"])
        upper = np.array(thresh["upper"])
        color_mask = cv2.inRange(hsv, lower, upper)
        return cv2.bitwise_and(color_mask, color_mask, mask=fish_mask)
    
    def _calculate_quality_score(
        self,
        hsv: np.ndarray,
        fish_mask: np.ndarray,
        white_mask: np.ndarray,
        red_mask: np.ndarray,
        black_mask: np.ndarray
    ) -> float:
        """
        Calculate overall color quality score.
        
        Quality is based on:
        1. Color saturation/vibrancy
        2. Edge sharpness between colors (Kiwa)
        3. Color consistency within patches
        
        Args:
            hsv: HSV image.
            fish_mask: Binary fish mask.
            white_mask: White area mask.
            red_mask: Red area mask.
            black_mask: Black area mask.
            
        Returns:
            Quality score between 0 and 1.
        """
        scores = []
        
        # 1. Saturation score for red areas (hi quality)
        saturation_score = self._calculate_saturation_score(hsv, red_mask)
        scores.append(saturation_score)
        
        # 2. Edge sharpness score (kiwa)
        edge_score = self._calculate_edge_sharpness(
            white_mask, red_mask, black_mask
        )
        scores.append(edge_score)
        
        # 3. Color consistency within patches
        consistency_score = self._calculate_color_consistency(
            hsv, white_mask, red_mask, black_mask
        )
        scores.append(consistency_score)
        
        # Weight the scores
        weights = [0.4, 0.35, 0.25]  # Saturation, edges, consistency
        quality = sum(s * w for s, w in zip(scores, weights))
        
        return min(max(quality, 0.0), 1.0)
    
    def _calculate_saturation_score(
        self,
        hsv: np.ndarray,
        red_mask: np.ndarray
    ) -> float:
        """Calculate color saturation score for red areas."""
        if np.sum(red_mask > 0) == 0:
            return 0.5  # Neutral score if no red
        
        # Extract saturation channel for red areas
        saturation = hsv[:, :, 1]
        red_saturation = saturation[red_mask > 0]
        
        # High saturation is desirable (closer to 255)
        mean_saturation = np.mean(red_saturation)
        score = mean_saturation / 255.0
        
        return score
    
    def _calculate_edge_sharpness(
        self,
        white_mask: np.ndarray,
        red_mask: np.ndarray,
        black_mask: np.ndarray
    ) -> float:
        """
        Calculate edge sharpness between color regions.
        Sharp edges (good kiwa) indicate higher quality.
        """
        # Combine all masks
        combined = (white_mask > 0).astype(np.uint8) * 1
        combined += (red_mask > 0).astype(np.uint8) * 2
        combined += (black_mask > 0).astype(np.uint8) * 3
        
        # Apply edge detection
        edges = cv2.Canny((combined * 50).astype(np.uint8), 50, 150)
        
        # Dilate edges slightly for comparison
        kernel = np.ones((3, 3), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Calculate edge sharpness as ratio of thin edges to dilated edges
        if np.sum(dilated_edges > 0) == 0:
            return 0.5
        
        edge_ratio = np.sum(edges > 0) / np.sum(dilated_edges > 0)
        
        # Map to 0-1 score (higher ratio = sharper edges)
        score = min(edge_ratio * 1.5, 1.0)
        
        return score
    
    def _calculate_color_consistency(
        self,
        hsv: np.ndarray,
        white_mask: np.ndarray,
        red_mask: np.ndarray,
        black_mask: np.ndarray
    ) -> float:
        """
        Calculate color consistency within each color region.
        Lower variance indicates more consistent, higher quality colors.
        """
        scores = []
        
        # Check white consistency (value channel)
        if np.sum(white_mask > 0) > 100:
            white_values = hsv[:, :, 2][white_mask > 0]
            white_std = np.std(white_values)
            # Lower std is better (max std would be ~73.5 for uniform)
            white_score = max(0, 1 - (white_std / 50))
            scores.append(white_score)
        
        # Check red consistency (hue and saturation)
        if np.sum(red_mask > 0) > 100:
            red_hues = hsv[:, :, 0][red_mask > 0]
            red_saturations = hsv[:, :, 1][red_mask > 0]
            # Handle hue wrap-around by converting to circular mean
            hue_std = np.std(red_hues)
            sat_std = np.std(red_saturations)
            red_score = max(0, 1 - ((hue_std + sat_std / 3) / 50))
            scores.append(red_score)
        
        # Check black consistency (value channel)
        if np.sum(black_mask > 0) > 100:
            black_values = hsv[:, :, 2][black_mask > 0]
            black_std = np.std(black_values)
            black_score = max(0, 1 - (black_std / 30))
            scores.append(black_score)
        
        if not scores:
            return 0.5
        
        return np.mean(scores)
    
    def get_color_visualization(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """
        Create a visualization of color segmentation.
        
        Args:
            image: Input image.
            mask: Fish segmentation mask.
            
        Returns:
            Visualization image with colored overlays.
        """
        # Apply mask to extract fish region
        fish_region = cv2.bitwise_and(image, image, mask=mask)
        hsv = cv2.cvtColor(fish_region, cv2.COLOR_BGR2HSV)
        
        # Create color masks
        white_mask = self._create_white_mask(hsv, mask)
        red_mask = self._create_red_mask(hsv, mask)
        black_mask = self._create_black_mask(hsv, mask)
        
        # Create visualization
        vis = image.copy()
        
        # Overlay colors
        vis[white_mask > 0] = [255, 255, 255]  # White
        vis[red_mask > 0] = [0, 0, 255]         # Red (BGR)
        vis[black_mask > 0] = [0, 0, 0]         # Black
        
        # Blend with original
        alpha = 0.5
        result = cv2.addWeighted(image, 1 - alpha, vis, alpha, 0)
        
        return result


# Global instance for reuse
_color_analyzer: Optional[ColorAnalyzer] = None


def get_color_analyzer() -> ColorAnalyzer:
    """Get or create the global ColorAnalyzer instance."""
    global _color_analyzer
    if _color_analyzer is None:
        _color_analyzer = ColorAnalyzer()
    return _color_analyzer


def analyze_fish_colors(
    image: np.ndarray,
    mask: np.ndarray
) -> Dict[str, float]:
    """
    Convenience function to analyze fish colors.
    
    Args:
        image: Input image as numpy array (BGR format).
        mask: Binary segmentation mask.
        
    Returns:
        Dictionary of color metrics.
    """
    analyzer = get_color_analyzer()
    return analyzer.analyze_colors(image, mask)
