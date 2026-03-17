"""
Symmetry Analysis Service

Measures bilateral symmetry of koi fish patterns using
PCA-based alignment and 5-section longitudinal comparison.
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Number of longitudinal sections for symmetry analysis (per MDPI paper)
_N_SECTIONS = 5

# Minimum pixels per section to attempt scoring
_MIN_SECTION_PIXELS = 5


class SymmetryAnalyzer:
    """
    Analyzes bilateral symmetry of koi fish patterns.

    Aligns the fish along its principal axis using PCA, then divides
    the body into 5 longitudinal sections. For each section, the
    color pattern area on the left and right sides of the midline
    are compared using the ratio formula from the MDPI paper:

        S_i = min(A_left_i, A_right_i) / max(A_left_i, A_right_i)

    The overall score is the mean across all sections:

        S_overall = mean(S_i for i in 1..5)
    """

    def analyze_symmetry(
        self,
        image: np.ndarray,
        mask: np.ndarray,
    ) -> float:
        """
        Calculate symmetry score for a koi fish.

        Args:
            image: Input image as numpy array (BGR format).
            mask: Binary segmentation mask.

        Returns:
            Symmetry score between 0 and 1 (1 = perfect symmetry).
        """
        aligned_image, aligned_mask = self._align_fish(image, mask)

        if aligned_image is None:
            logger.warning("Could not align fish for symmetry analysis")
            return 0.5

        score = self._score_longitudinal_symmetry(aligned_mask)
        logger.info(f"Calculated symmetry score: {score:.3f}")
        return score

    def _align_fish(
        self,
        image: np.ndarray,
        mask: np.ndarray,
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Align fish vertically using PCA on the mask.

        Args:
            image: Input image.
            mask: Binary mask.

        Returns:
            Tuple of (aligned image, aligned mask).
        """
        coords = np.argwhere(mask > 0)
        if len(coords) < 10:
            return None, None

        points = coords[:, ::-1].astype(np.float32)
        mean, eigenvectors = cv2.PCACompute(points, mean=None)

        angle = np.arctan2(eigenvectors[0, 1], eigenvectors[0, 0])
        rotation_angle = 90 - np.degrees(angle)

        center = (float(mean[0, 0]), float(mean[0, 1]))
        h, w = image.shape[:2]
        rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)

        cos_val = abs(np.cos(np.radians(rotation_angle)))
        sin_val = abs(np.sin(np.radians(rotation_angle)))
        new_w = int(h * sin_val + w * cos_val)
        new_h = int(h * cos_val + w * sin_val)

        rotation_matrix[0, 2] += (new_w - w) / 2
        rotation_matrix[1, 2] += (new_h - h) / 2

        aligned_image = cv2.warpAffine(
            image, rotation_matrix, (new_w, new_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0),
        )
        aligned_mask = cv2.warpAffine(
            mask, rotation_matrix, (new_w, new_h),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )

        aligned_image, aligned_mask = self._crop_to_content(aligned_image, aligned_mask)
        return aligned_image, aligned_mask

    def _crop_to_content(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        padding: int = 10,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crop image and mask to content region with optional padding.

        Args:
            image: Input image.
            mask: Binary mask.
            padding: Padding around content in pixels.

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

    def _score_longitudinal_symmetry(self, mask: np.ndarray) -> float:
        """
        Score symmetry by comparing left/right pixel counts across 5 sections.

        Divides the fish height into _N_SECTIONS equal longitudinal bands.
        For each band:
            S_i = min(left_pixels, right_pixels) / max(left_pixels, right_pixels)

        Sections with no pixels score 1.0 (trivially symmetric).

        Args:
            mask: Aligned binary segmentation mask.

        Returns:
            Mean section symmetry score between 0 and 1.
        """
        h, w = mask.shape[:2]
        section_height = h // _N_SECTIONS

        if section_height < _MIN_SECTION_PIXELS:
            logger.warning("Fish too small to score symmetry across 5 sections")
            return 0.5

        mid_x = w // 2
        section_scores = []

        for i in range(_N_SECTIONS):
            y_start = i * section_height
            y_end = h if i == _N_SECTIONS - 1 else y_start + section_height

            section = mask[y_start:y_end, :]
            left_pixels = int(np.sum(section[:, :mid_x] > 0))
            right_pixels = int(np.sum(section[:, mid_x:] > 0))

            max_pixels = max(left_pixels, right_pixels)
            if max_pixels == 0:
                section_scores.append(1.0)
            else:
                section_scores.append(min(left_pixels, right_pixels) / max_pixels)

        return float(np.mean(section_scores))

    def get_alignment_visualization(
        self,
        image: np.ndarray,
        mask: np.ndarray,
    ) -> np.ndarray:
        """
        Create visualization of the alignment and section divisions.

        Args:
            image: Input image.
            mask: Segmentation mask.

        Returns:
            Visualization image with midline and section boundaries drawn.
        """
        aligned_image, aligned_mask = self._align_fish(image, mask)

        if aligned_image is None:
            return image.copy()

        h, w = aligned_image.shape[:2]
        vis = aligned_image.copy()

        # Vertical midline
        cv2.line(vis, (w // 2, 0), (w // 2, h), (0, 255, 0), 2)

        # Horizontal section boundaries
        section_height = h // _N_SECTIONS
        for i in range(1, _N_SECTIONS):
            y = i * section_height
            cv2.line(vis, (0, y), (w, y), (0, 200, 255), 1)

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
    mask: np.ndarray,
) -> float:
    """
    Convenience function to analyze fish symmetry.

    Args:
        image: Input image as numpy array (BGR format).
        mask: Binary segmentation mask.

    Returns:
        Symmetry score between 0 and 1.
    """
    return get_symmetry_analyzer().analyze_symmetry(image, mask)
