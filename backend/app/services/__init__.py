"""
Services package

Contains all business logic services for koi fish appraisal:
- Size Detection: Calculates fish size using segmentation and reference coin
- Pattern Detection: Classifies koi patterns (Ogon, Showa, Kohaku)
- Color Analysis: Quantifies color distribution and quality
- Symmetry Analysis: Measures bilateral symmetry
- Price Prediction: Predicts price using trained linear regression model
"""

from app.services.size_detection import (
    SizeDetector,
    get_size_detector,
    detect_fish_size,
)
from app.services.pattern_detection import (
    PatternDetector,
    get_pattern_detector,
    classify_koi_pattern,
)
from app.services.color_analysis import (
    ColorAnalyzer,
    get_color_analyzer,
    analyze_fish_colors,
)
from app.services.symmetry_analysis import (
    SymmetryAnalyzer,
    get_symmetry_analyzer,
    analyze_fish_symmetry,
)
from app.services.price_prediction import (
    PricePredictor,
    get_price_predictor,
    predict_koi_price,
)

__all__ = [
    # Size Detection
    "SizeDetector",
    "get_size_detector",
    "detect_fish_size",
    # Pattern Detection
    "PatternDetector",
    "get_pattern_detector",
    "classify_koi_pattern",
    # Color Analysis
    "ColorAnalyzer",
    "get_color_analyzer",
    "analyze_fish_colors",
    # Symmetry Analysis
    "SymmetryAnalyzer",
    "get_symmetry_analyzer",
    "analyze_fish_symmetry",
    # Price Prediction
    "PricePredictor",
    "get_price_predictor",
    "predict_koi_price",
]
