"""
Color Scoring Service

Derives a quality score from color proportions based on
pattern-specific ideal distributions.
"""

from typing import Dict

# Ideal color distributions by pattern (percentages summing to 100)
_IDEAL_DISTRIBUTIONS: Dict[str, Dict[str, float]] = {
    "sanke":  {"Red": 50.0, "White": 30.0, "Black": 20.0},
    "kohaku": {"Red": 60.0, "White": 40.0},
}

# Maximum possible total absolute deviation between two distributions
# summing to 100 each (no overlap at all yields 200)
_MAX_TOTAL_DEVIATION = 200.0


def score_fish_colors(
    pattern_name: str,
    color_proportions: Dict[str, float],
) -> float:
    """
    Derive a color quality score based on pattern type and ideal distributions.

    Args:
        pattern_name: One of 'sanke', 'kohaku', 'ogon', or 'unknown'.
        color_proportions: Named color to percentage mapping from color analysis.

    Returns:
        Score between 0 and 1 (1 = perfect match to ideal distribution).
    """
    if pattern_name == "ogon":
        return _score_ogon(color_proportions)

    ideal = _IDEAL_DISTRIBUTIONS.get(pattern_name)
    if ideal is None:
        return 0.5

    return _score_against_ideal(color_proportions, ideal)


def _score_ogon(color_proportions: Dict[str, float]) -> float:
    """
    Score Ogon pattern (ideal = single uniform color covering 100%).

    The dominant color proportion divided by 100 gives the score.
    """
    if not color_proportions:
        return 0.0
    return max(color_proportions.values()) / 100.0


def _score_against_ideal(
    color_proportions: Dict[str, float],
    ideal: Dict[str, float],
) -> float:
    """
    Score actual color proportions against an ideal distribution.

    Totals the absolute deviation between actual and ideal percentages.
    Colors present in actual but absent in ideal contribute their full
    percentage as additional deviation.

    Args:
        color_proportions: Actual color percentages (values 0-100, sum ~100).
        ideal: Ideal color percentages (values 0-100, sum = 100).

    Returns:
        Score between 0 and 1.
    """
    total_deviation = 0.0

    for color, ideal_pct in ideal.items():
        actual_pct = color_proportions.get(color, 0.0)
        total_deviation += abs(actual_pct - ideal_pct)

    for color, actual_pct in color_proportions.items():
        if color not in ideal:
            total_deviation += actual_pct

    return max(0.0, 1.0 - total_deviation / _MAX_TOTAL_DEVIATION)
