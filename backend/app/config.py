"""
Application Configuration

Contains settings, constants, and coin size mappings.
"""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    DEBUG: bool = True
    MODEL_PATH: Path = Path("./models")
    IMAGES_PATH: Path = Path("./images")
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


# =============================================================================
# Philippine Peso Coin Specifications
# =============================================================================
# Reference: Bangko Sentral ng Pilipinas (BSP) official specifications
# Used for calculating Pixels Per Centimeter (PPC) in size detection
#
# Format: {class_name: {"diameter_mm": float, "diameter_cm": float}}
# Class names must match the trained coin detection model (coin.pt)
# =============================================================================

COIN_SIZES: dict[str, dict[str, float]] = {
    # ₱1 Peso Coins
    "1peso_new": {
        "diameter_mm": 23.0,
        "diameter_cm": 2.3,
        "weight_g": 6.0,
        "description": "NGC Series 2017-present",
    },
    "1peso_old": {
        "diameter_mm": 24.0,
        "diameter_cm": 2.4,
        "weight_g": 5.35,
        "description": "BSP Series 1995-2017",
    },
    
    # ₱5 Peso Coins
    "5peso_new": {
        "diameter_mm": 25.0,
        "diameter_cm": 2.5,
        "weight_g": 7.4,
        "description": "NGC Series 2017-present, Nonagonal (9-sided)",
    },
    "5peso_old": {
        "diameter_mm": 27.0,
        "diameter_cm": 2.7,
        "weight_g": 7.7,
        "description": "BSP Series 1995-2017",
    },
    
    # ₱10 Peso Coins
    "10peso_new": {
        "diameter_mm": 27.0,
        "diameter_cm": 2.7,
        "weight_g": 8.0,
        "description": "NGC Series 2017-present",
    },
    "10peso_old": {
        "diameter_mm": 27.0,
        "diameter_cm": 2.7,
        "weight_g": 8.0,
        "description": "BSP Series 2000-2017, Bi-metallic",
    },
    
    # ₱20 Peso Coin
    "20peso": {
        "diameter_mm": 30.0,
        "diameter_cm": 3.0,
        "weight_g": 11.5,
        "description": "Bi-metallic, 2019-present",
    },
}


def get_coin_diameter_cm(coin_class: str) -> float:
    """
    Get the diameter of a coin in centimeters.
    
    Args:
        coin_class: The class name from the coin detection model.
        
    Returns:
        Diameter in centimeters.
        
    Raises:
        ValueError: If coin class is not recognized.
    """
    if coin_class not in COIN_SIZES:
        raise ValueError(
            f"Unknown coin class: {coin_class}. "
            f"Valid classes: {list(COIN_SIZES.keys())}"
        )
    return COIN_SIZES[coin_class]["diameter_cm"]


def get_coin_diameter_mm(coin_class: str) -> float:
    """
    Get the diameter of a coin in millimeters.
    
    Args:
        coin_class: The class name from the coin detection model.
        
    Returns:
        Diameter in millimeters.
        
    Raises:
        ValueError: If coin class is not recognized.
    """
    if coin_class not in COIN_SIZES:
        raise ValueError(
            f"Unknown coin class: {coin_class}. "
            f"Valid classes: {list(COIN_SIZES.keys())}"
        )
    return COIN_SIZES[coin_class]["diameter_mm"]


# =============================================================================
# Koi Pattern Classes
# =============================================================================
# Must match the trained pattern classification model (koi-pattern.pt)
# =============================================================================

KOI_PATTERNS: list[str] = ["ogon", "showa", "kohaku"]


# =============================================================================
# Model File Paths
# =============================================================================

MODEL_PATHS = {
    "koi_segment": settings.MODEL_PATH / "koi-segment.pt",
    "coin_detect": settings.MODEL_PATH / "coin.pt",
    "koi_pattern": settings.MODEL_PATH / "koi-pattern.pt",
    "linear_regression": settings.MODEL_PATH / "linear.pkl",
}
