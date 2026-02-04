"""
Symmetry Analysis Service

Measures bilateral symmetry of koi fish patterns using
PCA-based alignment and Chi-squared comparison.
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class SymmetryAnalyzer:
    """
    Analyzes bilateral symmetry of koi fish patterns.
    
    Uses PCA to find the principal axis (handles bent fish),
    then compares left and right halves using statistical methods.
    """
    
    def __init__(self):
        """Initialize the symmetry analyzer."""
        pass
    
    def analyze_symmetry(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> float:
        """
        Calculate symmetry score for a koi fish.
        
        Args:
            image: Input image as numpy array (BGR format).
            mask: Binary segmentation mask.
            
        Returns:
            Symmetry score between 0 and 1 (1 = perfect symmetry).
        """
        # Align fish along principal axis
        aligned_image, aligned_mask = self._align_fish(image, mask)
        
        if aligned_image is None:
            logger.warning("Could not align fish for symmetry analysis")
            return 0.5  # Return neutral score
        
        # Split into left and right halves
        left_half, right_half = self._split_halves(aligned_image, aligned_mask)
        
        if left_half is None or right_half is None:
            logger.warning("Could not split fish into halves")
            return 0.5
        
        # Calculate symmetry score
        score = self._calculate_symmetry_score(left_half, right_half)
        
        logger.info(f"Calculated symmetry score: {score:.3f}")
        return score
    
    def _align_fish(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Align fish vertically using PCA on the mask.
        
        Args:
            image: Input image.
            mask: Binary mask.
            
        Returns:
            Tuple of (aligned image, aligned mask).
        """
        # Find contour points
        coords = np.argwhere(mask > 0)
        if len(coords) < 10:
            return None, None
        
        # Swap x and y for proper coordinates
        points = coords[:, ::-1].astype(np.float32)
        
        # Calculate PCA
        mean, eigenvectors = cv2.PCACompute(points, mean=None)
        
        # Principal axis angle
        angle = np.arctan2(eigenvectors[0, 1], eigenvectors[0, 0])
        angle_degrees = np.degrees(angle)
        
        # We want the fish to be vertical (head up)
        # Adjust angle to rotate to vertical
        rotation_angle = 90 - angle_degrees
        
        # Get center of mass
        center = tuple(mean[0].astype(int))
        
        # Create rotation matrix
        h, w = image.shape[:2]
        rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
        
        # Calculate new bounding box size to avoid cropping
        cos_val = abs(np.cos(np.radians(rotation_angle)))
        sin_val = abs(np.sin(np.radians(rotation_angle)))
        new_w = int(h * sin_val + w * cos_val)
        new_h = int(h * cos_val + w * sin_val)
        
        # Adjust rotation matrix for new size
        rotation_matrix[0, 2] += (new_w - w) / 2
        rotation_matrix[1, 2] += (new_h - h) / 2
        
        # Apply rotation
        aligned_image = cv2.warpAffine(
            image, rotation_matrix, (new_w, new_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0)
        )
        
        aligned_mask = cv2.warpAffine(
            mask, rotation_matrix, (new_w, new_h),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )
        
        # Crop to fish region
        aligned_image, aligned_mask = self._crop_to_content(
            aligned_image, aligned_mask
        )
        
        return aligned_image, aligned_mask
    
    def _crop_to_content(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        padding: int = 10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crop image and mask to content region.
        
        Args:
            image: Input image.
            mask: Binary mask.
            padding: Padding around content.
            
        Returns:
            Tuple of (cropped image, cropped mask).
        """
        coords = np.argwhere(mask > 0)
        if len(coords) == 0:
            return image, mask
        
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        
        h, w = image.shape[:2]
        y_min = max(0, y_min - padding)
        x_min = max(0, x_min - padding)
        y_max = min(h, y_max + padding)
        x_max = min(w, x_max + padding)
        
        return image[y_min:y_max, x_min:x_max], mask[y_min:y_max, x_min:x_max]
    
    def _split_halves(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Split aligned image into left and right halves.
        
        Args:
            image: Aligned image.
            mask: Aligned mask.
            
        Returns:
            Tuple of (left half, right half mirrored).
        """
        h, w = image.shape[:2]
        mid = w // 2
        
        # Split image
        left_img = image[:, :mid]
        right_img = image[:, mid:]
        
        # Split mask
        left_mask = mask[:, :mid]
        right_mask = mask[:, mid:]
        
        # Mirror right half for comparison
        right_img_mirrored = cv2.flip(right_img, 1)
        right_mask_mirrored = cv2.flip(right_mask, 1)
        
        # Ensure same size (handle odd widths)
        min_w = min(left_img.shape[1], right_img_mirrored.shape[1])
        left_img = left_img[:, :min_w]
        right_img_mirrored = right_img_mirrored[:, :min_w]
        left_mask = left_mask[:, :min_w]
        right_mask_mirrored = right_mask_mirrored[:, :min_w]
        
        # Apply masks
        left_masked = cv2.bitwise_and(left_img, left_img, mask=left_mask)
        right_masked = cv2.bitwise_and(
            right_img_mirrored, right_img_mirrored, mask=right_mask_mirrored
        )
        
        return left_masked, right_masked
    
    def _calculate_symmetry_score(
        self,
        left_half: np.ndarray,
        right_half: np.ndarray
    ) -> float:
        """
        Calculate symmetry score by comparing left and right halves.
        
        Uses multiple metrics:
        1. Pixel-wise color difference
        2. Histogram comparison
        3. Shape similarity (mask overlap)
        
        Args:
            left_half: Left half of fish (masked).
            right_half: Right half of fish (mirrored and masked).
            
        Returns:
            Symmetry score between 0 and 1.
        """
        scores = []
        
        # 1. Color histogram comparison
        hist_score = self._compare_color_histograms(left_half, right_half)
        scores.append(hist_score)
        
        # 2. Structural similarity
        struct_score = self._compare_structure(left_half, right_half)
        scores.append(struct_score)
        
        # 3. Pattern distribution similarity
        pattern_score = self._compare_pattern_distribution(left_half, right_half)
        scores.append(pattern_score)
        
        # Weighted average
        weights = [0.4, 0.3, 0.3]
        final_score = sum(s * w for s, w in zip(scores, weights))
        
        return min(max(final_score, 0.0), 1.0)
    
    def _compare_color_histograms(
        self,
        left: np.ndarray,
        right: np.ndarray
    ) -> float:
        """
        Compare color histograms of both halves.
        
        Uses correlation method for comparison.
        """
        # Convert to HSV for better color comparison
        left_hsv = cv2.cvtColor(left, cv2.COLOR_BGR2HSV)
        right_hsv = cv2.cvtColor(right, cv2.COLOR_BGR2HSV)
        
        # Calculate histograms
        hist_size = [30, 32, 32]  # H, S, V bins
        ranges = [0, 180, 0, 256, 0, 256]
        
        # Create mask for non-zero pixels
        left_gray = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
        right_gray = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)
        left_mask = (left_gray > 0).astype(np.uint8) * 255
        right_mask = (right_gray > 0).astype(np.uint8) * 255
        
        left_hist = cv2.calcHist(
            [left_hsv], [0, 1, 2], left_mask, hist_size, ranges
        )
        right_hist = cv2.calcHist(
            [right_hsv], [0, 1, 2], right_mask, hist_size, ranges
        )
        
        # Normalize histograms
        cv2.normalize(left_hist, left_hist)
        cv2.normalize(right_hist, right_hist)
        
        # Compare using correlation
        score = cv2.compareHist(left_hist, right_hist, cv2.HISTCMP_CORREL)
        
        # Map from [-1, 1] to [0, 1]
        return (score + 1) / 2
    
    def _compare_structure(
        self,
        left: np.ndarray,
        right: np.ndarray
    ) -> float:
        """
        Compare structural similarity of both halves.
        
        Uses edge detection and shape comparison.
        """
        # Convert to grayscale
        left_gray = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
        right_gray = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        left_edges = cv2.Canny(left_gray, 50, 150)
        right_edges = cv2.Canny(right_gray, 50, 150)
        
        # Compare edge patterns
        # XOR to find differences
        diff = cv2.bitwise_xor(left_edges, right_edges)
        
        # Calculate similarity
        total_edges = np.sum(left_edges > 0) + np.sum(right_edges > 0)
        if total_edges == 0:
            return 0.5
        
        diff_edges = np.sum(diff > 0)
        
        # Score based on how few differences there are
        score = 1 - (diff_edges / total_edges)
        
        return max(0, score)
    
    def _compare_pattern_distribution(
        self,
        left: np.ndarray,
        right: np.ndarray
    ) -> float:
        """
        Compare pattern distribution using Chi-squared test.
        
        Divides each half into grid cells and compares color distributions.
        """
        # Convert to HSV
        left_hsv = cv2.cvtColor(left, cv2.COLOR_BGR2HSV)
        right_hsv = cv2.cvtColor(right, cv2.COLOR_BGR2HSV)
        
        # Divide into grid (3x3)
        h, w = left_hsv.shape[:2]
        grid_h = h // 3
        grid_w = w // 3
        
        if grid_h < 10 or grid_w < 10:
            # Too small to analyze
            return 0.5
        
        scores = []
        
        for i in range(3):
            for j in range(3):
                y1, y2 = i * grid_h, (i + 1) * grid_h
                x1, x2 = j * grid_w, (j + 1) * grid_w
                
                left_cell = left_hsv[y1:y2, x1:x2]
                right_cell = right_hsv[y1:y2, x1:x2]
                
                # Get hue histograms
                left_hist = cv2.calcHist([left_cell], [0], None, [18], [0, 180])
                right_hist = cv2.calcHist([right_cell], [0], None, [18], [0, 180])
                
                # Add small value to avoid division by zero
                left_hist = left_hist.flatten() + 1
                right_hist = right_hist.flatten() + 1
                
                # Chi-squared statistic
                chi_sq = np.sum((left_hist - right_hist) ** 2 / (left_hist + right_hist))
                
                # Convert to similarity score
                # Lower chi-squared = more similar
                cell_score = 1 / (1 + chi_sq * 0.01)
                scores.append(cell_score)
        
        return np.mean(scores)
    
    def get_alignment_visualization(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """
        Create visualization of the alignment and symmetry analysis.
        
        Args:
            image: Input image.
            mask: Segmentation mask.
            
        Returns:
            Visualization image.
        """
        aligned_image, aligned_mask = self._align_fish(image, mask)
        
        if aligned_image is None:
            return image.copy()
        
        # Draw center line
        h, w = aligned_image.shape[:2]
        vis = aligned_image.copy()
        
        # Draw vertical center line
        cv2.line(vis, (w // 2, 0), (w // 2, h), (0, 255, 0), 2)
        
        return vis


# Global instance for reuse
_symmetry_analyzer: Optional[SymmetryAnalyzer] = None


def get_symmetry_analyzer() -> SymmetryAnalyzer:
    """Get or create the global SymmetryAnalyzer instance."""
    global _symmetry_analyzer
    if _symmetry_analyzer is None:
        _symmetry_analyzer = SymmetryAnalyzer()
    return _symmetry_analyzer


def analyze_fish_symmetry(
    image: np.ndarray,
    mask: np.ndarray
) -> float:
    """
    Convenience function to analyze fish symmetry.
    
    Args:
        image: Input image as numpy array (BGR format).
        mask: Binary segmentation mask.
        
    Returns:
        Symmetry score between 0 and 1.
    """
    analyzer = get_symmetry_analyzer()
    return analyzer.analyze_symmetry(image, mask)
