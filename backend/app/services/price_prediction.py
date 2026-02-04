"""
Price Prediction Service

Predicts koi fish prices using a trained linear regression model.
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
    using a trained linear regression model.
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize the price predictor.
        
        Args:
            model_path: Path to the trained model file.
        """
        self.model_path = model_path or MODEL_PATHS["linear_regression"]
        self._model = None
        self._scaler = None
        self._feature_names = None
        self._loaded = False
    
    def _load_model(self) -> None:
        """Load the trained model from disk."""
        if self._loaded:
            return
        
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Price prediction model not found at {self.model_path}. "
                "Please train the model first using: python -m app.train --csv <path>"
            )
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self._model = model_data['model']
            self._scaler = model_data['scaler']
            self._feature_names = model_data.get('feature_names', [])
            self._loaded = True
            
            logger.info(f"Loaded price prediction model from {self.model_path}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def predict(
        self,
        size_cm: float,
        pattern_name: str,
        pattern_confidence: float,
        color_white_pct: float,
        color_red_pct: float,
        color_black_pct: float,
        color_quality_score: float,
        symmetry_score: float
    ) -> float:
        """
        Predict the price of a koi fish based on its metrics.
        
        Args:
            size_cm: Fish size in centimeters.
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
        self._load_model()
        
        # Build feature vector
        features = self._build_feature_vector(
            size_cm=size_cm,
            pattern_name=pattern_name,
            pattern_confidence=pattern_confidence,
            color_white_pct=color_white_pct,
            color_red_pct=color_red_pct,
            color_black_pct=color_black_pct,
            color_quality_score=color_quality_score,
            symmetry_score=symmetry_score
        )
        
        # Scale features
        features_scaled = self._scaler.transform([features])
        
        # Predict
        prediction = self._model.predict(features_scaled)[0]
        
        # Ensure non-negative price
        prediction = max(0.0, prediction)
        
        logger.info(f"Predicted price: {prediction:.2f}")
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
            size_cm=metrics['size_cm'],
            pattern_name=metrics['pattern_name'],
            pattern_confidence=metrics['pattern_confidence'],
            color_white_pct=metrics['color_white_pct'],
            color_red_pct=metrics['color_red_pct'],
            color_black_pct=metrics['color_black_pct'],
            color_quality_score=metrics['color_quality_score'],
            symmetry_score=metrics['symmetry_score']
        )
    
    def _build_feature_vector(
        self,
        size_cm: float,
        pattern_name: str,
        pattern_confidence: float,
        color_white_pct: float,
        color_red_pct: float,
        color_black_pct: float,
        color_quality_score: float,
        symmetry_score: float
    ) -> list:
        """
        Build the feature vector for prediction.
        
        Must match the feature order used during training.
        """
        # One-hot encode pattern
        pattern_ogon = 1.0 if pattern_name.lower() == 'ogon' else 0.0
        pattern_showa = 1.0 if pattern_name.lower() == 'showa' else 0.0
        pattern_kohaku = 1.0 if pattern_name.lower() == 'kohaku' else 0.0
        
        features = [
            size_cm,
            pattern_ogon,
            pattern_showa,
            pattern_kohaku,
            pattern_confidence,
            color_white_pct,
            color_red_pct,
            color_black_pct,
            color_quality_score,
            symmetry_score
        ]
        
        return features
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get the feature importance (coefficients) from the model.
        
        Returns:
            Dictionary mapping feature names to their coefficients.
        """
        self._load_model()
        
        if not self._feature_names:
            return {}
        
        importance = dict(zip(self._feature_names, self._model.coef_))
        importance['intercept'] = self._model.intercept_
        
        return importance
    
    def is_model_available(self) -> bool:
        """Check if the trained model is available."""
        return self.model_path.exists()


# Global instance for reuse
_price_predictor: Optional[PricePredictor] = None


def get_price_predictor() -> PricePredictor:
    """Get or create the global PricePredictor instance."""
    global _price_predictor
    if _price_predictor is None:
        _price_predictor = PricePredictor()
    return _price_predictor


def predict_koi_price(
    size_cm: float,
    pattern_name: str,
    pattern_confidence: float,
    color_white_pct: float,
    color_red_pct: float,
    color_black_pct: float,
    color_quality_score: float,
    symmetry_score: float
) -> float:
    """
    Convenience function to predict koi fish price.
    
    Args:
        Various metrics from fish analysis.
        
    Returns:
        Predicted price.
    """
    predictor = get_price_predictor()
    return predictor.predict(
        size_cm=size_cm,
        pattern_name=pattern_name,
        pattern_confidence=pattern_confidence,
        color_white_pct=color_white_pct,
        color_red_pct=color_red_pct,
        color_black_pct=color_black_pct,
        color_quality_score=color_quality_score,
        symmetry_score=symmetry_score
    )
