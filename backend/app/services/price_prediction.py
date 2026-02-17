"""
Price Prediction Service

Predicts koi fish prices using per-pattern trained linear regression models.
Each koi pattern (ogon, showa, kohaku) has its own dedicated model.
"""

import logging
import pickle
from pathlib import Path
from typing import Dict, Optional

import numpy as np

from app.config import MODEL_PATHS, KOI_PATTERNS

logger = logging.getLogger(__name__)


class PricePredictor:
    """
    Predicts koi fish prices based on extracted metrics
    using pattern-specific linear regression models.

    One model is loaded per pattern type (ogon, showa, kohaku).
    The correct model is selected at prediction time based on
    the detected pattern name.
    """

    def __init__(self):
        """Initialize the price predictor with lazy-loaded pattern models."""
        # Pattern → loaded model data (lazy)
        self._models: Dict[str, dict] = {}

    # ------------------------------------------------------------------ #
    #  Model loading
    # ------------------------------------------------------------------ #

    def _model_path_for(self, pattern_name: str) -> Path:
        """Return the expected .pkl path for a given pattern."""
        key = f"linear_{pattern_name}"
        path = MODEL_PATHS.get(key)
        if path is None:
            raise ValueError(
                f"No model path configured for pattern '{pattern_name}'. "
                f"Valid patterns: {KOI_PATTERNS}"
            )
        return path

    def _load_model(self, pattern_name: str) -> dict:
        """
        Load (or return cached) model data for a pattern.

        Args:
            pattern_name: One of 'ogon', 'showa', 'kohaku'.

        Returns:
            Dict with keys 'model', 'scaler', 'feature_names'.
        """
        pattern = pattern_name.lower()

        if pattern in self._models:
            return self._models[pattern]

        model_path = self._model_path_for(pattern)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Price prediction model for '{pattern}' not found at "
                f"{model_path}. Train it first using: "
                f"python -m app.train --{pattern}-csv <path> "
                f"--{pattern}-images <dir> ..."
            )

        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)

            self._models[pattern] = model_data
            logger.info(
                f"Loaded price prediction model for '{pattern}' "
                f"from {model_path}"
            )
            return model_data

        except Exception as e:
            raise RuntimeError(
                f"Failed to load model for '{pattern}': {e}"
            )

    # ------------------------------------------------------------------ #
    #  Prediction
    # ------------------------------------------------------------------ #

    def predict(
        self,
        pattern_name: str,
        pattern_confidence: float,
        color_white_pct: float,
        color_red_pct: float,
        color_black_pct: float,
        color_quality_score: float,
        symmetry_score: float,
    ) -> float:
        """
        Predict the price of a koi fish based on its metrics.

        Automatically selects the model trained for the given pattern.
        Size is not used because training images lack reference coins.

        Args:
            pattern_name: Pattern name (ogon, showa, kohaku).
            pattern_confidence: Pattern classification confidence.
            color_white_pct: Percentage of white color.
            color_red_pct: Percentage of red color.
            color_black_pct: Percentage of black color.
            color_quality_score: Color quality score (0-1).
            symmetry_score: Bilateral symmetry score (0-1).

        Returns:
            Predicted price.
        """
        pattern = pattern_name.lower()
        model_data = self._load_model(pattern)

        model = model_data['model']
        scaler = model_data['scaler']

        features = self._build_feature_vector(
            pattern_confidence=pattern_confidence,
            color_white_pct=color_white_pct,
            color_red_pct=color_red_pct,
            color_black_pct=color_black_pct,
            color_quality_score=color_quality_score,
            symmetry_score=symmetry_score,
        )

        features_scaled = scaler.transform([features])
        prediction = model.predict(features_scaled)[0]

        # Ensure non-negative price
        prediction = max(0.0, prediction)

        logger.info(
            f"Predicted price for '{pattern}': {prediction:.2f}"
        )
        return float(prediction)

    def predict_from_dict(self, metrics: Dict) -> float:
        """
        Predict price from a metrics dictionary.

        Args:
            metrics: Dictionary containing all required metrics.

        Returns:
            Predicted price.
        """
        return self.predict(
            pattern_name=metrics['pattern_name'],
            pattern_confidence=metrics['pattern_confidence'],
            color_white_pct=metrics['color_white_pct'],
            color_red_pct=metrics['color_red_pct'],
            color_black_pct=metrics['color_black_pct'],
            color_quality_score=metrics['color_quality_score'],
            symmetry_score=metrics['symmetry_score'],
        )

    @staticmethod
    def _build_feature_vector(
        pattern_confidence: float,
        color_white_pct: float,
        color_red_pct: float,
        color_black_pct: float,
        color_quality_score: float,
        symmetry_score: float,
    ) -> list:
        """
        Build the feature vector for prediction.

        Must match the feature order used during per-pattern training.
        Size is excluded (training images lack reference coins).
        """
        return [
            pattern_confidence,
            color_white_pct,
            color_red_pct,
            color_black_pct,
            color_quality_score,
            symmetry_score,
        ]

    def get_feature_importance(self, pattern_name: str) -> Dict[str, float]:
        """
        Get the feature importance (coefficients) for a pattern's model.

        Args:
            pattern_name: One of 'ogon', 'showa', 'kohaku'.

        Returns:
            Dictionary mapping feature names to their coefficients.
        """
        model_data = self._load_model(pattern_name.lower())
        feature_names = model_data.get('feature_names', [])
        model = model_data['model']

        if not feature_names:
            return {}

        importance = dict(zip(feature_names, model.coef_))
        importance['intercept'] = model.intercept_
        return importance

    def is_model_available(self, pattern_name: Optional[str] = None) -> bool:
        """
        Check if trained model(s) are available.

        Args:
            pattern_name: Check a specific pattern, or ``None`` to check all.

        Returns:
            True if the requested model(s) exist on disk.
        """
        if pattern_name:
            return self._model_path_for(pattern_name.lower()).exists()

        return all(
            self._model_path_for(p).exists() for p in KOI_PATTERNS
        )


# Global instance for reuse
_price_predictor: Optional[PricePredictor] = None


def get_price_predictor() -> PricePredictor:
    """Get or create the global PricePredictor instance."""
    global _price_predictor
    if _price_predictor is None:
        _price_predictor = PricePredictor()
    return _price_predictor


def predict_koi_price(
    pattern_name: str,
    pattern_confidence: float,
    color_white_pct: float,
    color_red_pct: float,
    color_black_pct: float,
    color_quality_score: float,
    symmetry_score: float,
) -> float:
    """
    Convenience function to predict koi fish price.

    Automatically selects the correct per-pattern model.

    Args:
        Various metrics from fish analysis.

    Returns:
        Predicted price.
    """
    predictor = get_price_predictor()
    return predictor.predict(
        pattern_name=pattern_name,
        pattern_confidence=pattern_confidence,
        color_white_pct=color_white_pct,
        color_red_pct=color_red_pct,
        color_black_pct=color_black_pct,
        color_quality_score=color_quality_score,
        symmetry_score=symmetry_score,
    )
