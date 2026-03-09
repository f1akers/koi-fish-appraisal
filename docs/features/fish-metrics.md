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

### 1.3 Color Analysis (Refactored — spec 003)

**Purpose:** Quantify the color distribution of the koi fish using palette-based clustering.

**Implementation Steps:**

1. Extract masked fish pixels via segmentation mask (`mask > 0`)
2. Convert BGR → CIELAB colorspace (`cv2.cvtColor(image, cv2.COLOR_BGR2Lab)`)
3. Reshape to `(N, 3)` float64 array
4. Cluster with `sklearn.cluster.KMeans(n_clusters=4, random_state=42, n_init=1)`
5. Map cluster centroids to named koi colors using `KOI_COLOR_MAP` (static LAB centroids in config.py)
6. Assign colors via Euclidean distance to nearest centroid (threshold `COLOR_DISTANCE_THRESHOLD=50.0` for "Other" fallback)
7. Merge duplicate color mappings and return proportions

**Named Colors:** White, Red, Black, Orange, Yellow, Other

**Edge Cases:**

- Fewer than 10 pixels → warning log + single-cluster fallback
- Unmapped centroids beyond threshold → "Other"

**Input:** Image (numpy array), segmentation mask  
**Output:** `Dict[str, float]` — Named color proportions summing to ~100%

**Files:**

- `backend/app/services/color_analysis.py`
- `backend/app/config.py` (KOI_COLOR_MAP, DEFAULT_K_CLUSTERS, COLOR_DISTANCE_THRESHOLD)

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

### 1.5 Multi-Sample Aggregation (Added — spec 003)

**Purpose:** Run pattern and size detection multiple times per image with input-level augmentation for more reliable results.

**Implementation:**

- **Augmentation:** Mild brightness/contrast jitter (±10%), small rotation (±5°), 50% horizontal flip; seed=0 returns original unaugmented image
- **Pattern aggregation:** Majority vote across N samples, mean confidence of winning votes
- **Size aggregation:** `np.median()` of N size measurements; representative mask selected from run closest to median
- **Default:** `n_samples=3` (configurable via `DEFAULT_N_SAMPLES` in config.py)
- **Backward-compatible:** `n_samples=1` produces identical behavior to single-pass

**Files:**

- `backend/app/services/pattern_detection.py` (augment_image + multi-sample wrapper)
- `backend/app/services/size_detection.py` (multi-sample wrapper)
- `backend/app/routers/appraisal.py` (pipeline orchestration)

---

## API Endpoint

```python
@router.post("/appraise")
async def appraise_koi(image: UploadFile) -> AppraisalResponse:
    """
    Process uploaded koi fish image and return appraisal.

    Returns:
        AppraisalResponse containing size, pattern, color_proportions, symmetry
    """
```

**Response format:**

```json
{
  "size_cm": 25.4,
  "pattern_name": "kohaku",
  "pattern_confidence": 0.92,
  "color_proportions": { "Red": 42.3, "White": 35.1, "Black": 22.6 },
  "symmetry_score": 0.87
}
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

| File                                        | Purpose                                                 |
| ------------------------------------------- | ------------------------------------------------------- |
| `backend/app/services/size_detection.py`    | Fish size detection using segmentation + coin reference |
| `backend/app/services/pattern_detection.py` | Pattern classification (Ogon, Showa, Kohaku)            |
| `backend/app/services/color_analysis.py`    | K-Means clustering color distribution in CIELAB         |
| `backend/app/services/symmetry_analysis.py` | Bilateral symmetry measurement using PCA                |

### Removed Files (spec 003)

| File                                           | Reason                                      |
| ---------------------------------------------- | ------------------------------------------- |
| `backend/app/services/price_prediction.py`     | Price prediction removed                    |
| `backend/app/services/color_calibration_ui.py` | HSV calibration UI replaced by LAB approach |
| `backend/app/train.py`                         | Training script for price model removed     |
| `backend/models/linear*.pkl/json`              | Price model artifacts removed               |

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
