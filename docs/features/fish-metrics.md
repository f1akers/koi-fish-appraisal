# Feature 1: Fish Metrics

**Status:** 🔴 Not Started  
**Last Updated:** -

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

- [ ] Size detection with various coin positions
- [ ] Size detection with different coin denominations
- [ ] Pattern classification for each pattern type
- [ ] Color analysis produces consistent results
- [ ] Symmetry analysis handles bent fish correctly
- [ ] End-to-end appraisal pipeline works

---

## Completion Checklist

When this feature is complete:
- [ ] All sub-features implemented and tested
- [ ] API endpoint created and documented
- [ ] Unit tests written with >80% coverage
- [ ] Error handling implemented
- [ ] Update status in FEATURES_INDEX.md to 🟢
- [ ] Document any configuration changes
