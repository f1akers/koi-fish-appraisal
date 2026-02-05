"""
Application Configuration

Contains settings, constants, and coin size mappings.
"""

from pathlib import Path
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    DEBUG: bool = True
    MODEL_PATH: Path = Path("./models")
    IMAGES_PATH: Path = Path("./images")
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get ALLOWED_ORIGINS as a list of strings."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


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

# =============================================================================
# Coin Class Name Mapping
# =============================================================================
# Maps model output class names to COIN_SIZES keys
# The coin.pt model outputs names like "1 peso new front", "1 peso old back", etc.
# =============================================================================

COIN_CLASS_MAP: dict[str, str] = {
    # 1 Peso New
    "1 peso new front": "1peso_new",
    "1 peso new back": "1peso_new",
    "1peso new front": "1peso_new",
    "1peso new back": "1peso_new",
    # 1 Peso Old
    "1 peso old front": "1peso_old",
    "1 peso old back": "1peso_old",
    "1peso old front": "1peso_old",
    "1peso old back": "1peso_old",
    # 5 Peso New
    "5 peso new front": "5peso_new",
    "5 peso new back": "5peso_new",
    "5peso new front": "5peso_new",
    "5peso new back": "5peso_new",
    # 5 Peso Old
    "5 peso old front": "5peso_old",
    "5 peso old back": "5peso_old",
    "5peso old front": "5peso_old",
    "5peso old back": "5peso_old",
    # 10 Peso New
    "10 peso new front": "10peso_new",
    "10 peso new back": "10peso_new",
    "10peso new front": "10peso_new",
    "10peso new back": "10peso_new",
    # 10 Peso Old
    "10 peso old front": "10peso_old",
    "10 peso old back": "10peso_old",
    "10peso old front": "10peso_old",
    "10peso old back": "10peso_old",
    # 20 Peso
    "20 peso front": "20peso",
    "20 peso back": "20peso",
    "20peso front": "20peso",
    "20peso back": "20peso",
}


def normalize_coin_class(coin_class: str) -> str:
    """
    Normalize coin class name from model output to COIN_SIZES key.
    
    Args:
        coin_class: The class name from the coin detection model.
        
    Returns:
        Normalized class name matching COIN_SIZES keys.
        
    Raises:
        ValueError: If coin class cannot be normalized.
    """
    # First check if it's already a valid key
    if coin_class in COIN_SIZES:
        return coin_class
    
    # Try to map from model output format
    normalized = COIN_CLASS_MAP.get(coin_class.lower())
    if normalized:
        return normalized
    
    raise ValueError(
        f"Unknown coin class: {coin_class}. "
        f"Valid classes: {list(COIN_SIZES.keys())}"
    )


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
    normalized = normalize_coin_class(coin_class)
    return COIN_SIZES[normalized]["diameter_cm"]


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
    normalized = normalize_coin_class(coin_class)
    return COIN_SIZES[normalized]["diameter_mm"]


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
