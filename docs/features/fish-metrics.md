# Feature 1: Fish Metrics

**Status:** � Completed  
**Last Updated:** February 5, 2026

---

## Overview

This feature extracts numerical metrics from koi fish images that will be used as input for the price prediction model. All metrics return numerical values suitable for linear regression training.

---

## Sub-features

### 1.1 Size Detection

**Purpose:** Calculate the actual size of the koi fish in centimeters.

**Implementation Steps:**
1. Load the koi segmentation model (`backend/models/koi-segment.pt`)
2. Run inference to get instance segmentation mask
3. Count pixels within the segmentation mask
4. Load coin detection model (`backend/models/coin.pt`)
5. Detect reference coin in the image
6. Look up coin's actual diameter from `config.py` (coin sizes mapping)
7. Calculate Pixels Per Centimeter (PPC) = `coin_pixels / coin_diameter_cm`
8. Calculate fish size = `fish_pixels / PPC`

**Input:** Image (numpy array or file path)  
**Output:** `float` - Size in centimeters

**Files to Create/Modify:**
- `backend/app/services/size_detection.py`

---

### 1.2 Pattern Recognition

**Purpose:** Classify the koi fish pattern into one of three types.

**Pattern Types:**
| Pattern | Class Name | Description |
|---------|------------|-------------|
| Ogon | `ogon` | Solid metallic color |
| Showa | `showa` | Black, red, and white |
| Kohaku | `kohaku` | White with red markings |

**Implementation Steps:**
1. Load pattern classification model (`backend/models/koi-pattern.pt`)
2. Run inference on the fish region
3. Return predicted class and confidence score

**Input:** Image (numpy array or file path)  
**Output:** `tuple(str, float)` - (pattern_name, confidence)

**Files to Create/Modify:**
- `backend/app/services/pattern_detection.py`

---

### 1.3 Color Analysis

**Purpose:** Quantify the color distribution and quality of the koi fish.

**Implementation Steps:**
1. Extract the fish region using segmentation mask
2. Convert to appropriate color space (HSV recommended)
3. Define color ranges for:
   - White
   - Red/Orange (Hi)
   - Black (Sumi)
4. Calculate percentage of each color
5. Apply quality scoring based on:
   - Color intensity/vibrancy
   - Edge sharpness between colors (Kiwa)
   - Color depth consistency

**Scoring Criteria (to be refined with research):**
- Color saturation levels
- Color boundary clarity
- Even distribution within color patches

**Input:** Image (numpy array), segmentation mask  
**Output:** `dict` - Color metrics dictionary

**Files to Create/Modify:**
- `backend/app/services/color_analysis.py`

---

### 1.4 Symmetry Analysis

**Purpose:** Measure the bilateral symmetry of the koi fish pattern.

**Implementation Steps:**
1. Extract fish region using segmentation mask
2. Apply PCA to find the principal axis (accounts for bent fish)
3. Rotate/align fish along principal axis
4. Split into left and right halves
5. Compare halves using Chi-squared test
6. Return symmetry score (0-1, where 1 is perfect symmetry)

**Algorithm:**
```
1. Get segmentation mask
2. Find centroid and orientation using PCA
3. Align fish to vertical axis
4. Mirror one half
5. Calculate Chi-squared distance between halves
6. Normalize to symmetry score
```

**Input:** Image (numpy array), segmentation mask  
**Output:** `float` - Symmetry score (0-1)

**Files to Create/Modify:**
- `backend/app/services/symmetry_analysis.py`

---

### 1.5 Price Prediction

**Purpose:** Predict the price based on collected metrics.

**Implementation Steps:**
1. Collect all metrics: size, pattern, color scores, symmetry
2. Prepare feature vector
3. Load trained linear regression model (`backend/models/linear.pkl`)
4. Run prediction
5. Return predicted price

**Input:** `dict` - All collected metrics  
**Output:** `float` - Predicted price

**Files to Create/Modify:**
- `backend/app/services/price_prediction.py`

---

## API Endpoint

```python
@router.post("/appraise")
async def appraise_koi(image: UploadFile) -> AppraisalResult:
    """
    Process uploaded koi fish image and return appraisal.
    
    Returns:
        AppraisalResult containing all metrics and predicted price
    """
```

---

## Testing Checklist

- [x] Size detection with various coin positions
- [x] Size detection with different coin denominations
- [x] Pattern classification for each pattern type
- [x] Color analysis produces consistent results
- [x] Symmetry analysis handles bent fish correctly
- [x] End-to-end appraisal pipeline works

---

## Completion Checklist

When this feature is complete:
- [x] All sub-features implemented and tested
- [x] API endpoint created and documented
- [ ] Unit tests written with >80% coverage
- [x] Error handling implemented
- [x] Update status in FEATURES_INDEX.md to 🟢
- [x] Document any configuration changes

---

## Implementation Summary

### Files Created

| File | Purpose |
|------|---------|
| `backend/app/services/size_detection.py` | Fish size detection using segmentation + coin reference |
| `backend/app/services/pattern_detection.py` | Pattern classification (Ogon, Showa, Kohaku) |
| `backend/app/services/color_analysis.py` | Color distribution and quality analysis |
| `backend/app/services/color_calibration_ui.py` | Optional calibration UI for color thresholds |
| `backend/app/services/symmetry_analysis.py` | Bilateral symmetry measurement using PCA |
| `backend/app/services/price_prediction.py` | Price prediction using trained model |
| `backend/app/train.py` | Linear regression model training script |

### Color Calibration

A calibration UI is available for adjusting color detection thresholds if needed:

```bash
python -m app.services.color_calibration_ui [optional_image_path]
```

Calibration settings are saved to `backend/models/color_calibration.json`.

### Training the Model

```bash
# From backend directory
python -m app.train --csv images/training_data.csv

# With custom options
python -m app.train --csv data.csv --output models/custom.pkl --val-split 0.3
```

### API Usage

```bash
# Appraise an image
curl -X POST "http://localhost:8000/api/appraise" \
  -H "accept: application/json" \
  -F "image=@koi_fish.jpg"

# Train the model
curl -X POST "http://localhost:8000/api/train?csv_path=images/training.csv"

# Check model status
curl "http://localhost:8000/api/model-status"
```
