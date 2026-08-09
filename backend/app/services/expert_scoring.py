"""
Expert Scoring Service

Predicts expert-calibrated quality scores (color, pattern, symmetry,
overall) from the vision pipeline features using per-pattern-type
XGBoost regressors trained by app/train.py.

Models are lazy-loaded singletons saved as XGBoost JSON in
`models/expert/<type>_<target>.json`. Predictions are on the expert
1-5 rating scale and are converted to 0-1 at the API boundary.
"""

import logging
from pathlib import Path

import numpy as np
from xgboost import XGBRegressor

from app.config import (
    EXPERT_MODEL_DIR,
    EXPERT_SCORE_MAX,
    EXPERT_SCORE_MIN,
    EXPERT_TARGETS,
    KOI_PATTERNS,
)
from app.utils.feature_extraction import FEATURE_COLUMNS

logger = logging.getLogger(__name__)


class ExpertScoringService:
    """
    Loads and runs the per-type expert-scoring XGBoost models.
    """

    def __init__(self, models_dir=None):
        """Initialize with no models loaded (lazy)."""
        self._models_dir = Path(models_dir or EXPERT_MODEL_DIR)
        self._models: dict[str, dict[str, XGBRegressor]] | None = None
        self._feature_columns: list[str] = FEATURE_COLUMNS
        self._score_min = EXPERT_SCORE_MIN
        self._score_max = EXPERT_SCORE_MAX

    @property
    def models(self) -> dict[str, dict[str, XGBRegressor]]:
        """Lazy-load per-type models for all trained pattern types."""
        if self._models is None:
            self._models = {}
            for pattern_type in KOI_PATTERNS:
                if self._type_models_available(pattern_type):
                    self._models[pattern_type] = self._load_type(pattern_type)
            logger.info(
                f"Loaded expert scoring models from {self._models_dir}: "
                f"{sorted(self._models.keys())}"
            )
        return self._models

    def _type_models_available(self, pattern_type: str) -> bool:
        """Check that all targets exist for one pattern type."""
        return all(
            (self._models_dir / f"{pattern_type}_{target}.json").exists()
            for target in EXPERT_TARGETS
        )

    def _load_type(self, pattern_type: str) -> dict[str, XGBRegressor]:
        """
        Load all target models for one pattern type.

        Raises:
            FileNotFoundError: If any model file for the type is missing.
        """
        type_models = {}
        for target in EXPERT_TARGETS:
            path = self._models_dir / f"{pattern_type}_{target}.json"
            if not path.exists():
                raise FileNotFoundError(
                    f"Expert scoring model not found at {path}. "
                    f"Run `python -m app.train` first."
                )
            model = XGBRegressor()
            model.load_model(str(path))
            type_models[target] = model
        return type_models

    def is_available(self) -> bool:
        """Check whether a complete model set exists for any pattern type."""
        return any(self._type_models_available(t) for t in KOI_PATTERNS)

    def predict(
        self,
        pattern_name: str,
        features: dict[str, float],
    ) -> dict[str, float]:
        """
        Predict expert-calibrated scores for one appraisal.

        Args:
            pattern_name: Detected pattern ('ogon', 'sanke', 'kohaku').
            features: Feature dictionary with FEATURE_COLUMNS keys.

        Returns:
            Dictionary mapping each target (color, pattern, symmetry,
            overall) to a 0-1 score.

        Raises:
            FileNotFoundError: If models for the pattern type are not trained.
            ValueError: If the pattern type is unknown.
        """
        if pattern_name not in KOI_PATTERNS:
            raise ValueError(f"Unknown pattern '{pattern_name}'")
        type_models = self._load_type(pattern_name)

        vector = np.array(
            [features.get(col, 0.0) for col in self._feature_columns],
            dtype=float,
        ).reshape(1, -1)

        stage1: dict[str, float] = {}
        for target in ("color", "pattern", "symmetry"):
            raw = float(type_models[target].predict(vector)[0])
            stage1[target] = self._clip(raw)

        overall_input = np.hstack([vector, np.array([[stage1[t] for t in ("color", "pattern", "symmetry")]])])
        raw_overall = float(type_models["overall"].predict(overall_input)[0])

        scores = {**stage1, "overall": self._clip(raw_overall)}
        return {target: (value - self._score_min) / (self._score_max - self._score_min) for target, value in scores.items()}

    def _clip(self, value: float) -> float:
        """Clip a raw prediction to the expert 1-5 scale."""
        return float(np.clip(value, self._score_min, self._score_max))


# Global instance for reuse
_expert_scoring: ExpertScoringService | None = None


def get_expert_scoring() -> ExpertScoringService:
    """Get or create the global ExpertScoringService instance."""
    global _expert_scoring
    if _expert_scoring is None:
        _expert_scoring = ExpertScoringService()
    return _expert_scoring
