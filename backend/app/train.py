"""
Linear Regression Trainer

Training script for the koi fish price prediction model.
Extracts features from labeled images and trains a linear regression model.
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
from app.services.size_detection import detect_fish_size
from app.services.pattern_detection import classify_koi_pattern
from app.services.color_analysis import analyze_fish_colors
from app.services.symmetry_analysis import analyze_fish_symmetry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KoiPriceTrainer:
    """
    Trains a linear regression model for koi fish price prediction.
    
    Extracts features from labeled images and trains a model that
    predicts price based on size, pattern, color, and symmetry metrics.
    """
    
    def __init__(
        self,
        images_dir: Optional[Path] = None,
        output_path: Optional[Path] = None
    ):
        """
        Initialize the trainer.
        
        Args:
            images_dir: Directory containing training images.
            output_path: Path to save the trained model.
        """
        self.images_dir = images_dir or settings.IMAGES_PATH
        self.output_path = output_path or MODEL_PATHS["linear_regression"]
        
        self.model: Optional[LinearRegression] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        
        # Training data
        self.features: List[List[float]] = []
        self.labels: List[float] = []
        self.failed_images: List[Tuple[str, str]] = []
    
    def load_training_data(self, csv_path: str) -> int:
        """
        Load training data from CSV file.
        
        Args:
            csv_path: Path to CSV file with columns: image_filename, price
            
        Returns:
            Number of successfully loaded samples.
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        logger.info(f"Loading training data from {csv_path}")
        
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                image_filename = row.get('image_filename', '').strip()
                price_str = row.get('price', '').strip()
                
                if not image_filename or not price_str:
                    logger.warning(f"Skipping invalid row: {row}")
                    continue
                
                try:
                    price = float(price_str)
                except ValueError:
                    logger.warning(f"Invalid price value: {price_str}")
                    continue
                
                # Load and process image
                image_path = self.images_dir / image_filename
                if not image_path.exists():
                    logger.warning(f"Image not found: {image_path}")
                    self.failed_images.append((image_filename, "File not found"))
                    continue
                
                # Extract features
                features = self._extract_features(image_path)
                
                if features is None:
                    self.failed_images.append((image_filename, "Feature extraction failed"))
                    continue
                
                self.features.append(features)
                self.labels.append(price)
                
                logger.info(f"Processed: {image_filename} (price: {price})")
        
        logger.info(
            f"Loaded {len(self.features)} samples, "
            f"{len(self.failed_images)} failed"
        )
        
        return len(self.features)
    
    def _extract_features(self, image_path: Path) -> Optional[List[float]]:
        """
        Extract feature vector from a single image.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            List of feature values, or None if extraction failed.
        """
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Could not read image: {image_path}")
                return None
            
            # 1. Size detection (also gets segmentation mask)
            try:
                size_cm, mask, size_info = detect_fish_size(image)
            except Exception as e:
                logger.error(f"Size detection failed: {e}")
                return None
            
            # 2. Pattern recognition
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
                    "quality_score": 0.0
                }
            
            # 4. Symmetry analysis
            try:
                symmetry_score = analyze_fish_symmetry(image, mask)
            except Exception as e:
                logger.warning(f"Symmetry analysis failed: {e}")
                symmetry_score = 0.5
            
            # Build feature vector
            features = self._build_feature_vector(
                size_cm=size_cm,
                pattern_name=pattern_name,
                pattern_confidence=pattern_conf,
                color_metrics=color_metrics,
                symmetry_score=symmetry_score
            )
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction error for {image_path}: {e}")
            return None
    
    def _build_feature_vector(
        self,
        size_cm: float,
        pattern_name: str,
        pattern_confidence: float,
        color_metrics: Dict[str, float],
        symmetry_score: float
    ) -> List[float]:
        """
        Build the feature vector for model training.
        
        Features:
        - size_cm: Fish size in centimeters
        - pattern_ogon, pattern_showa, pattern_kohaku: One-hot encoded pattern
        - pattern_confidence: Pattern classification confidence
        - color_white_pct: Percentage of white
        - color_red_pct: Percentage of red
        - color_black_pct: Percentage of black
        - color_quality_score: Color quality score
        - symmetry_score: Bilateral symmetry score
        
        Args:
            Various metrics from feature extraction.
            
        Returns:
            List of feature values.
        """
        # Set feature names on first call
        if not self.feature_names:
            self.feature_names = [
                'size_cm',
                'pattern_ogon',
                'pattern_showa',
                'pattern_kohaku',
                'pattern_confidence',
                'color_white_pct',
                'color_red_pct',
                'color_black_pct',
                'color_quality_score',
                'symmetry_score'
            ]
        
        # One-hot encode pattern
        pattern_ogon = 1.0 if pattern_name == 'ogon' else 0.0
        pattern_showa = 1.0 if pattern_name == 'showa' else 0.0
        pattern_kohaku = 1.0 if pattern_name == 'kohaku' else 0.0
        
        features = [
            size_cm,
            pattern_ogon,
            pattern_showa,
            pattern_kohaku,
            pattern_confidence,
            color_metrics['white_pct'],
            color_metrics['red_pct'],
            color_metrics['black_pct'],
            color_metrics['quality_score'],
            symmetry_score
        ]
        
        return features
    
    def train(
        self,
        validation_split: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, float]:
        """
        Train the linear regression model.
        
        Args:
            validation_split: Fraction of data to use for validation.
            random_state: Random seed for reproducibility.
            
        Returns:
            Dictionary of training metrics.
        """
        if len(self.features) < 5:
            raise ValueError(
                f"Not enough training samples: {len(self.features)}. "
                "Need at least 5 samples."
            )
        
        logger.info(f"Training model with {len(self.features)} samples...")
        
        X = np.array(self.features)
        y = np.array(self.labels)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=random_state
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train model
        self.model = LinearRegression()
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate on validation set
        y_pred = self.model.predict(X_val_scaled)
        
        metrics = {
            'r2_score': r2_score(y_val, y_pred),
            'mae': mean_absolute_error(y_val, y_pred),
            'mse': mean_squared_error(y_val, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_val, y_pred)),
            'samples_trained': len(X_train),
            'samples_validated': len(X_val)
        }
        
        logger.info(f"Training complete. Metrics: {metrics}")
        
        # Log feature importances (coefficients)
        logger.info("\nFeature Coefficients:")
        for name, coef in zip(self.feature_names, self.model.coef_):
            logger.info(f"  {name}: {coef:.4f}")
        logger.info(f"  Intercept: {self.model.intercept_:.4f}")
        
        return metrics
    
    def save_model(self) -> None:
        """Save the trained model and scaler to disk."""
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")
        
        # Create output directory if needed
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model and scaler together
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'trained_at': datetime.now().isoformat(),
            'samples_trained': len(self.features)
        }
        
        with open(self.output_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {self.output_path}")
    
    def save_training_report(self, metrics: Dict[str, float]) -> None:
        """
        Save a training report with metrics and configuration.
        
        Args:
            metrics: Training metrics dictionary.
        """
        report_path = self.output_path.with_suffix('.json')
        
        report = {
            'trained_at': datetime.now().isoformat(),
            'samples_total': len(self.features) + len(self.failed_images),
            'samples_successful': len(self.features),
            'samples_failed': len(self.failed_images),
            'metrics': metrics,
            'feature_names': self.feature_names,
            'feature_coefficients': dict(
                zip(self.feature_names, self.model.coef_.tolist())
            ) if self.model else {},
            'intercept': float(self.model.intercept_) if self.model else 0.0,
            'failed_images': self.failed_images
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Training report saved to {report_path}")


def train_model(
    csv_path: str,
    output_path: Optional[str] = None,
    validation_split: float = 0.2
) -> Dict[str, float]:
    """
    Main function to train the price prediction model.
    
    Args:
        csv_path: Path to CSV file with training data.
        output_path: Optional custom output path for model.
        validation_split: Fraction for validation (default 0.2).
        
    Returns:
        Training metrics dictionary.
    """
    trainer = KoiPriceTrainer(
        output_path=Path(output_path) if output_path else None
    )
    
    # Load data
    num_samples = trainer.load_training_data(csv_path)
    
    if num_samples == 0:
        raise ValueError("No valid training samples found.")
    
    # Train model
    metrics = trainer.train(validation_split=validation_split)
    
    # Save model and report
    trainer.save_model()
    trainer.save_training_report(metrics)
    
    return metrics


def main():
    """CLI entry point for training."""
    parser = argparse.ArgumentParser(
        description="Train koi fish price prediction model"
    )
    parser.add_argument(
        '--csv', '-c',
        required=True,
        help="Path to CSV file with columns: image_filename, price"
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help="Output path for trained model (default: models/linear.pkl)"
    )
    parser.add_argument(
        '--val-split', '-v',
        type=float,
        default=0.2,
        help="Validation split fraction (default: 0.2)"
    )
    
    args = parser.parse_args()
    
    try:
        metrics = train_model(
            csv_path=args.csv,
            output_path=args.output,
            validation_split=args.val_split
        )
        
        print("\n" + "=" * 50)
        print("Training Complete!")
        print("=" * 50)
        print(f"R² Score:         {metrics['r2_score']:.4f}")
        print(f"MAE:              {metrics['mae']:.2f}")
        print(f"RMSE:             {metrics['rmse']:.2f}")
        print(f"Samples Trained:  {metrics['samples_trained']}")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
