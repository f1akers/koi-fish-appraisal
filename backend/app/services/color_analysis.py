"""
Color Analysis Service

Quantifies color distribution of koi fish patterns using
K-Means clustering in CIELAB colorspace with named color mapping.
"""

import logging
from typing import Dict

import cv2
import numpy as np
from sklearn.cluster import KMeans

from app.config import (
    DEFAULT_K_CLUSTERS,
    COLOR_DISTANCE_THRESHOLD,
    KMEANS_RANDOM_SEED,
    KOI_COLOR_MAP,
)

logger = logging.getLogger(__name__)


def _map_centroid_to_color(centroid: np.ndarray) -> str:
    """
    Map a LAB cluster centroid to the nearest named koi color.

    Args:
        centroid: 1-D array of (L, a, b) in OpenCV uint8 encoding.

    Returns:
        Named color string, or "Other" if beyond threshold.
    """
    best_name = "Other"
    best_dist = COLOR_DISTANCE_THRESHOLD

    for name, lab_tuple in KOI_COLOR_MAP.items():
        ref = np.array(lab_tuple, dtype=np.float64)
        dist = float(np.linalg.norm(centroid - ref))
        if dist < best_dist:
            best_dist = dist
            best_name = name

    return best_name


def analyze_fish_colors(
    image: np.ndarray,
    mask: np.ndarray,
    k: int = DEFAULT_K_CLUSTERS,
) -> Dict[str, float]:
    """
    Analyze color distribution within the fish region using K-Means
    clustering in CIELAB colorspace.

    Extracts masked fish pixels, converts BGR -> LAB, clusters with
    K-Means, maps cluster centroids to named koi colors, and returns
    proportions summing to ~100%.

    Args:
        image: Input image as numpy array (BGR format).
        mask: Binary segmentation mask (same H x W as image).
        k: Number of K-Means clusters (default from config).

    Returns:
        Dictionary mapping named colors to percentages (e.g.
        ``{"Red": 42.3, "White": 35.1, "Black": 22.6}``).
        Only colors with > 0% are included.
    """
    # Convert to LAB colorspace
    lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)

    # Extract fish pixels using the mask
    fish_pixels = lab_image[mask > 0]  # shape: (N, 3)

    if len(fish_pixels) == 0:
        logger.warning("No fish pixels found in mask - returning empty proportions")
        return {"Other": 100.0}

    # Edge case: very few pixels -> single-cluster fallback
    if len(fish_pixels) < 10:
        logger.warning(
            f"Only {len(fish_pixels)} fish pixels - falling back to single cluster"
        )
        effective_k = 1
    else:
        effective_k = min(k, len(fish_pixels))

    fish_pixels_f = fish_pixels.astype(np.float64)

    # Run K-Means clustering
    kmeans = KMeans(
        n_clusters=effective_k,
        random_state=KMEANS_RANDOM_SEED,
        n_init=1,
    )
    labels = kmeans.fit_predict(fish_pixels_f)
    centroids = kmeans.cluster_centers_  # shape: (k, 3)

    # Map each cluster centroid to a named koi color
    color_counts: Dict[str, int] = {}
    total_pixels = len(labels)

    for cluster_idx in range(effective_k):
        color_name = _map_centroid_to_color(centroids[cluster_idx])
        count = int(np.sum(labels == cluster_idx))
        color_counts[color_name] = color_counts.get(color_name, 0) + count

    # Convert counts to percentages
    proportions: Dict[str, float] = {}
    for name, count in color_counts.items():
        pct = (count / total_pixels) * 100.0
        if pct > 0:
            proportions[name] = round(pct, 1)

    logger.info(f"Color analysis: {proportions}")
    return proportions
