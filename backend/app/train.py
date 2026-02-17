"""
Linear Regression Trainer (Per-Pattern)

Training script for koi fish price prediction models.
Trains separate linear regression models for each koi pattern type
(ogon, sanke, kohaku) using pattern-specific training data.

Usage:
    python -m app.train \
        --ogon-csv <path> --ogon-images <dir> \
        --sanke-csv <path> --sanke-images <dir> \
        --kohaku-csv <path> --kohaku-images <dir>
"""

import argparse
import csv
import json
import logging
import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings, MODEL_PATHS, KOI_PATTERNS
from app.services.size_detection import detect_fish_mask
from app.services.pattern_detection import classify_koi_pattern
from app.services.color_analysis import analyze_fish_colors
from app.services.symmetry_analysis import analyze_fish_symmetry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Feature names for per-pattern models
# Size is excluded because training images typically lack a reference coin.
FEATURE_NAMES: List[str] = [
    'pattern_confidence',
    'color_white_pct',
    'color_red_pct',
    'color_black_pct',
    'color_quality_score',
    'symmetry_score',
]


class KoiPatternTrainer:
    """
    Trains a linear regression model for a single koi pattern type.

    Since each pattern gets its own model, the feature vector excludes
    pattern one-hot encoding — only size, color, symmetry, and
    pattern-confidence features are used.
    """

    def __init__(
        self,
        pattern_name: str,
        images_dir: Path,
        output_path: Optional[Path] = None,
    ):
        """
        Initialize the per-pattern trainer.

        Args:
            pattern_name: One of 'ogon', 'sanke', 'kohaku'.
            images_dir: Directory containing this pattern's training images.
            output_path: Path to save the trained model (.pkl).
        """
        if pattern_name not in KOI_PATTERNS:
            raise ValueError(
                f"Invalid pattern '{pattern_name}'. "
                f"Must be one of {KOI_PATTERNS}"
            )

        self.pattern_name = pattern_name
        self.images_dir = Path(images_dir)
        self.output_path = (
            output_path
            or MODEL_PATHS[f"linear_{pattern_name}"]
        )

        self.model: Optional[LinearRegression] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = list(FEATURE_NAMES)

        # Training data
        self.features: List[List[float]] = []
        self.labels: List[float] = []
        self.failed_images: List[Tuple[str, str]] = []

    # --------------------------------------------------------------------- #
    #  Data loading
    # --------------------------------------------------------------------- #

    def load_training_data(self, csv_path: str) -> int:
        """
        Load training data from a CSV file.

        The CSV must have columns: ``image_filename``, ``price``.

        Args:
            csv_path: Path to the CSV file.

        Returns:
            Number of successfully loaded samples.
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        logger.info(
            f"[{self.pattern_name}] Loading training data from {csv_path}"
        )

        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                image_filename = row.get('image_filename', '').strip()
                price_str = row.get('price', '').strip()

                if not image_filename or not price_str:
                    logger.warning(
                        f"[{self.pattern_name}] Skipping invalid row: {row}"
                    )
                    continue

                try:
                    price = float(price_str)
                except ValueError:
                    logger.warning(
                        f"[{self.pattern_name}] Invalid price value: "
                        f"{price_str}"
                    )
                    continue

                image_path = self.images_dir / image_filename
                if not image_path.exists():
                    logger.warning(
                        f"[{self.pattern_name}] Image not found: {image_path}"
                    )
                    self.failed_images.append(
                        (image_filename, "File not found")
                    )
                    continue

                features = self._extract_features(image_path)

                if features is None:
                    self.failed_images.append(
                        (image_filename, "Feature extraction failed")
                    )
                    continue

                self.features.append(features)
                self.labels.append(price)

                logger.info(
                    f"[{self.pattern_name}] Processed: {image_filename} "
                    f"(price: {price})"
                )

        logger.info(
            f"[{self.pattern_name}] Loaded {len(self.features)} samples, "
            f"{len(self.failed_images)} failed"
        )

        return len(self.features)

    # --------------------------------------------------------------------- #
    #  Feature extraction
    # --------------------------------------------------------------------- #

    def _extract_features(self, image_path: Path) -> Optional[List[float]]:
        """
        Extract feature vector from a single image.

        Args:
            image_path: Path to the image file.

        Returns:
            List of feature values, or ``None`` if extraction failed.
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Could not read image: {image_path}")
                return None

            # 1. Fish segmentation (mask only — no coin/size needed)
            try:
                mask, pixel_count = detect_fish_mask(image)
                if mask is None:
                    logger.error(f"No fish detected in {image_path}")
                    return None
            except Exception as e:
                logger.error(f"Fish segmentation failed: {e}")
                return None

            # 2. Pattern recognition — still run to capture confidence
            try:
                pattern_name, pattern_conf = classify_koi_pattern(image, mask)
            except Exception as e:
                logger.warning(f"Pattern detection failed: {e}")
                pattern_name, pattern_conf = "unknown", 0.0

            # 3. Color analysis
            try:
                color_metrics = analyze_fish_colors(image, mask)
            except Exception as e:
                logger.warning(f"Color analysis failed: {e}")
                color_metrics = {
                    "white_pct": 0.0,
                    "red_pct": 0.0,
                    "black_pct": 0.0,
                    "quality_score": 0.0,
                }

            # 4. Symmetry analysis
            try:
                symmetry_score = analyze_fish_symmetry(image, mask)
            except Exception as e:
                logger.warning(f"Symmetry analysis failed: {e}")
                symmetry_score = 0.5

            return self._build_feature_vector(
                pattern_confidence=pattern_conf,
                color_metrics=color_metrics,
                symmetry_score=symmetry_score,
            )

        except Exception as e:
            logger.error(
                f"Feature extraction error for {image_path}: {e}"
            )
            return None

    @staticmethod
    def _build_feature_vector(
        pattern_confidence: float,
        color_metrics: Dict[str, float],
        symmetry_score: float,
    ) -> List[float]:
        """
        Build the feature vector for a per-pattern model.

        Size is excluded because training images typically lack a
        reference coin.  Features (in order):

        - ``pattern_confidence``
        - ``color_white_pct``
        - ``color_red_pct``
        - ``color_black_pct``
        - ``color_quality_score``
        - ``symmetry_score``
        """
        return [
            pattern_confidence,
            color_metrics['white_pct'],
            color_metrics['red_pct'],
            color_metrics['black_pct'],
            color_metrics['quality_score'],
            symmetry_score,
        ]

    # --------------------------------------------------------------------- #
    #  Training
    # --------------------------------------------------------------------- #

    def train(
        self,
        validation_split: float = 0.2,
        random_state: int = 42,
    ) -> Dict[str, float]:
        """
        Train the linear regression model.

        Args:
            validation_split: Fraction of data for validation.
            random_state: Random seed for reproducibility.

        Returns:
            Dictionary of training metrics.
        """
        if len(self.features) < 5:
            raise ValueError(
                f"[{self.pattern_name}] Not enough training samples: "
                f"{len(self.features)}. Need at least 5."
            )

        logger.info(
            f"[{self.pattern_name}] Training model with "
            f"{len(self.features)} samples..."
        )

        X = np.array(self.features)
        y = np.array(self.labels)

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=random_state
        )

        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        self.model = LinearRegression()
        self.model.fit(X_train_scaled, y_train)

        y_pred = self.model.predict(X_val_scaled)

        metrics = {
            'r2_score': r2_score(y_val, y_pred),
            'mae': mean_absolute_error(y_val, y_pred),
            'mse': mean_squared_error(y_val, y_pred),
            'rmse': float(np.sqrt(mean_squared_error(y_val, y_pred))),
            'samples_trained': len(X_train),
            'samples_validated': len(X_val),
        }

        logger.info(
            f"[{self.pattern_name}] Training complete. Metrics: {metrics}"
        )

        logger.info(f"\n[{self.pattern_name}] Feature Coefficients:")
        for name, coef in zip(self.feature_names, self.model.coef_):
            logger.info(f"  {name}: {coef:.4f}")
        logger.info(f"  Intercept: {self.model.intercept_:.4f}")

        return metrics

    # --------------------------------------------------------------------- #
    #  Persistence
    # --------------------------------------------------------------------- #

    def save_model(self) -> None:
        """Save the trained model and scaler to disk."""
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'pattern': self.pattern_name,
            'trained_at': datetime.now().isoformat(),
            'samples_trained': len(self.features),
        }

        with open(self.output_path, 'wb') as f:
            pickle.dump(model_data, f)

        logger.info(
            f"[{self.pattern_name}] Model saved to {self.output_path}"
        )

    def save_training_report(self, metrics: Dict[str, float]) -> None:
        """
        Save a JSON training report.

        Args:
            metrics: Training metrics dictionary.
        """
        report_path = self.output_path.with_suffix('.json')

        report = {
            'pattern': self.pattern_name,
            'trained_at': datetime.now().isoformat(),
            'samples_total': len(self.features) + len(self.failed_images),
            'samples_successful': len(self.features),
            'samples_failed': len(self.failed_images),
            'metrics': metrics,
            'feature_names': self.feature_names,
            'feature_coefficients': dict(
                zip(self.feature_names, self.model.coef_.tolist())
            ) if self.model else {},
            'intercept': (
                float(self.model.intercept_) if self.model else 0.0
            ),
            'failed_images': self.failed_images,
        }

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(
            f"[{self.pattern_name}] Training report saved to {report_path}"
        )


# ========================================================================= #
#  Public helpers
# ========================================================================= #

def train_pattern_model(
    pattern_name: str,
    csv_path: str,
    images_dir: str,
    output_path: Optional[str] = None,
    validation_split: float = 0.2,
) -> Dict[str, float]:
    """
    Train a single per-pattern price prediction model.

    Args:
        pattern_name: One of 'ogon', 'sanke', 'kohaku'.
        csv_path: Path to the CSV with columns ``image_filename``, ``price``.
        images_dir: Directory containing training images for this pattern.
        output_path: Optional custom output path for the model file.
        validation_split: Fraction for validation (default 0.2).

    Returns:
        Training metrics dictionary.
    """
    trainer = KoiPatternTrainer(
        pattern_name=pattern_name,
        images_dir=Path(images_dir),
        output_path=Path(output_path) if output_path else None,
    )

    num_samples = trainer.load_training_data(csv_path)

    if num_samples == 0:
        raise ValueError(
            f"[{pattern_name}] No valid training samples found."
        )

    metrics = trainer.train(validation_split=validation_split)

    trainer.save_model()
    trainer.save_training_report(metrics)

    return metrics


def train_all_patterns(
    pattern_configs: Dict[str, Dict[str, str]],
    validation_split: float = 0.2,
) -> Dict[str, Dict[str, float]]:
    """
    Train models for all koi patterns.

    Args:
        pattern_configs: Mapping of pattern name to config dict with keys
            ``csv_path`` and ``images_dir``.
        validation_split: Fraction for validation (default 0.2).

    Returns:
        Mapping of pattern name to training metrics dict.
    """
    all_metrics: Dict[str, Dict[str, float]] = {}

    for pattern in KOI_PATTERNS:
        cfg = pattern_configs.get(pattern)
        if cfg is None:
            logger.warning(
                f"No config supplied for pattern '{pattern}' — skipping."
            )
            continue

        logger.info(f"\n{'=' * 60}")
        logger.info(f"Training model for pattern: {pattern}")
        logger.info(f"{'=' * 60}")

        metrics = train_pattern_model(
            pattern_name=pattern,
            csv_path=cfg['csv_path'],
            images_dir=cfg['images_dir'],
            validation_split=validation_split,
        )
        all_metrics[pattern] = metrics

    return all_metrics


# ========================================================================= #
#  CLI
# ========================================================================= #

def main():
    """CLI entry point for per-pattern training."""
    parser = argparse.ArgumentParser(
        description=(
            "Train koi fish price prediction models — "
            "one linear regression per pattern type."
        )
    )

    # Ogon
    parser.add_argument(
        '--ogon-csv',
        required=True,
        help="Path to CSV for ogon (columns: image_filename, price)",
    )
    parser.add_argument(
        '--ogon-images',
        required=True,
        help="Directory containing ogon training images",
    )

    # Sanke
    parser.add_argument(
        '--sanke-csv',
        required=True,
        help="Path to CSV for sanke (columns: image_filename, price)",
    )
    parser.add_argument(
        '--sanke-images',
        required=True,
        help="Directory containing sanke training images",
    )

    # Kohaku
    parser.add_argument(
        '--kohaku-csv',
        required=True,
        help="Path to CSV for kohaku (columns: image_filename, price)",
    )
    parser.add_argument(
        '--kohaku-images',
        required=True,
        help="Directory containing kohaku training images",
    )

    # Optional
    parser.add_argument(
        '--val-split', '-v',
        type=float,
        default=0.2,
        help="Validation split fraction (default: 0.2)",
    )

    args = parser.parse_args()

    pattern_configs = {
        'ogon': {
            'csv_path': args.ogon_csv,
            'images_dir': args.ogon_images,
        },
        'sanke': {
            'csv_path': args.sanke_csv,
            'images_dir': args.sanke_images,
        },
        'kohaku': {
            'csv_path': args.kohaku_csv,
            'images_dir': args.kohaku_images,
        },
    }

    try:
        all_metrics = train_all_patterns(
            pattern_configs=pattern_configs,
            validation_split=args.val_split,
        )

        print("\n" + "=" * 60)
        print("Training Complete — All Patterns")
        print("=" * 60)

        for pattern, metrics in all_metrics.items():
            print(f"\n  [{pattern.upper()}]")
            print(f"    R² Score:         {metrics['r2_score']:.4f}")
            print(f"    MAE:              {metrics['mae']:.2f}")
            print(f"    RMSE:             {metrics['rmse']:.2f}")
            print(f"    Samples Trained:  {metrics['samples_trained']}")

        print("\n" + "=" * 60)

    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
