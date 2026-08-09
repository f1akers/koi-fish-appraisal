"""
Expert Scoring Tests

Covers feature vector assembly and the ExpertScoringService using
small in-memory XGBoost models (no YOLO models required).
"""

import numpy as np
import pytest
from xgboost import XGBRegressor

from app.config import EXPERT_TARGETS
from app.services.expert_scoring import ExpertScoringService
from app.utils.feature_extraction import FEATURE_COLUMNS, build_feature_vector


def _save_synthetic_models(models_dir, seed=7):
    """Train and save tiny per-type models for one pattern type."""
    rng = np.random.default_rng(seed)
    X = rng.random((200, len(FEATURE_COLUMNS)))
    stage1 = {}
    for target in ("color", "pattern", "symmetry"):
        model = XGBRegressor(n_estimators=20, max_depth=2)
        model.fit(X, rng.uniform(1, 5, 200))
        model.save_model(str(models_dir / f"kohaku_{target}.json"))
        stage1[target] = model.predict(X)
    overall = XGBRegressor(n_estimators=20, max_depth=2)
    overall.fit(np.hstack([X, np.column_stack(list(stage1.values()))]), rng.uniform(1, 5, 200))
    overall.save_model(str(models_dir / "kohaku_overall.json"))


def test_build_feature_vector_keys():
    """Feature vector must contain exactly the canonical columns."""
    features = build_feature_vector(
        pattern_name="sanke",
        pattern_confidence=0.9,
        symmetry_score=0.75,
        color_proportions={"Red": 50.0, "White": 30.0, "Black": 20.0},
    )
    assert set(features.keys()) == set(FEATURE_COLUMNS)


def test_build_feature_vector_one_hot():
    """One-hot pattern flags and heuristic color prior are correct."""
    features = build_feature_vector(
        pattern_name="sanke",
        pattern_confidence=0.9,
        symmetry_score=0.75,
        color_proportions={"Red": 50.0, "White": 30.0, "Black": 20.0},
    )
    assert features["pattern_sanke"] == 1.0
    assert features["pattern_ogon"] == 0.0
    assert features["pattern_kohaku"] == 0.0
    assert features["pattern_confidence"] == 0.9
    assert features["symmetry_score"] == 0.75
    assert features["color_Red"] == 50.0
    assert features["color_Orange"] == 0.0
    assert 0.0 <= features["color_score"] <= 1.0


def test_build_feature_vector_unknown_pattern():
    """Unknown pattern yields all-zero one-hot flags."""
    features = build_feature_vector(
        pattern_name="unknown",
        pattern_confidence=0.0,
        symmetry_score=0.5,
        color_proportions={"Other": 100.0},
    )
    assert features["pattern_sanke"] == 0.0
    assert features["pattern_ogon"] == 0.0
    assert features["pattern_kohaku"] == 0.0


def test_expert_scoring_predicts_all_targets(tmp_path):
    """Service loads per-type models and returns 0-1 scores for all targets."""
    _save_synthetic_models(tmp_path)
    service = ExpertScoringService(models_dir=tmp_path)

    features = build_feature_vector(
        pattern_name="kohaku",
        pattern_confidence=0.8,
        symmetry_score=0.8,
        color_proportions={"Red": 60.0, "White": 40.0},
    )
    scores = service.predict("kohaku", features)

    assert set(scores.keys()) == set(EXPERT_TARGETS)
    for score in scores.values():
        assert 0.0 <= score <= 1.0


def test_expert_scoring_missing_models_raises(tmp_path):
    """Predict raises FileNotFoundError when models are not trained."""
    service = ExpertScoringService(models_dir=tmp_path)
    features = build_feature_vector(
        pattern_name="ogon",
        pattern_confidence=0.5,
        symmetry_score=0.5,
        color_proportions={"White": 100.0},
    )
    with pytest.raises(FileNotFoundError):
        service.predict("ogon", features)


def test_expert_scoring_unknown_pattern_raises(tmp_path):
    """Predict raises ValueError for pattern names outside KOI_PATTERNS."""
    _save_synthetic_models(tmp_path)
    service = ExpertScoringService(models_dir=tmp_path)
    features = build_feature_vector(
        pattern_name="unknown",
        pattern_confidence=0.5,
        symmetry_score=0.5,
        color_proportions={"White": 100.0},
    )
    with pytest.raises(ValueError):
        service.predict("unknown", features)
