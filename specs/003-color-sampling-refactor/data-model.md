# Data Model: Color & Sampling Refactor

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)
**Date**: 2026-03-09

---

## Entities

### 1. ColorProportion

Represents a named koi color paired with its percentage of total fish pixels. Replaces the previous fixed three-color fields (`white_pct`, `red_pct`, `black_pct`).

| Field | Type   | Constraints     | Description                                                |
| ----- | ------ | --------------- | ---------------------------------------------------------- |
| name  | string | non-empty       | Named koi color (Red, White, Black, Orange, Yellow, Other) |
| pct   | float  | 0.0 ≤ x ≤ 100.0 | Percentage of total fish pixels for this color             |

**Validation**: All proportions in a result MUST sum to ~100% (±1% rounding tolerance per SC-001).

**Representation in API**: Returned as `Dict[str, float]` where keys are color names and values are percentages. Example: `{"Red": 42.3, "White": 35.1, "Black": 22.6}`.

---

### 2. KoiColorMapEntry

A reference entry in the static color mapping table used to classify LAB cluster centroids to named koi colors.

| Field | Type   | Constraints | Description                                      |
| ----- | ------ | ----------- | ------------------------------------------------ |
| name  | string | non-empty   | Named koi color                                  |
| lab_l | int    | 0–255       | CIELAB L\* channel (OpenCV uint8 encoding)       |
| lab_a | int    | 0–255       | CIELAB a\* channel (OpenCV uint8, offset by 128) |
| lab_b | int    | 0–255       | CIELAB b\* channel (OpenCV uint8, offset by 128) |

**Static data** (defined in `config.py` or as module constant):

| Name   | L\* | a\* | b\* | Notes                                        |
| ------ | --- | --- | --- | -------------------------------------------- |
| White  | 245 | 128 | 128 | Near-neutral, very high lightness (Shiroji)  |
| Red    | 140 | 185 | 175 | High a* (red), moderate b* (Hi)              |
| Black  | 30  | 128 | 128 | Near-neutral, very low lightness (Sumi)      |
| Orange | 175 | 170 | 190 | Moderate-high L*, positive a* and b\* (Beni) |
| Yellow | 220 | 118 | 200 | High L*, slight negative a*, strong b\* (Ki) |

**Distance threshold**: 50.0 units in uint8 LAB space. Centroids farther than this from all named colors → "Other".

---

### 3. InferenceSample (conceptual — not persisted)

A single run of an ML model on one image variant. Used internally by the multi-sample aggregation logic.

| Field              | Type       | Description                                       |
| ------------------ | ---------- | ------------------------------------------------- |
| sample_index       | int        | 0-based index of this sample (0 = original image) |
| augmented_image    | np.ndarray | The (possibly augmented) input image              |
| pattern_name       | string     | Pattern classification result for this sample     |
| pattern_confidence | float      | Classification confidence for this sample         |
| size_cm            | float      | Size measurement for this sample                  |
| mask               | np.ndarray | Segmentation mask for this sample                 |

**Not persisted** — exists only during the appraisal pipeline execution.

---

### 4. AggregatedResult (conceptual — maps to AppraisalResponse)

The final combined output from multiple inference samples.

| Field              | Type             | Aggregation Method                                        |
| ------------------ | ---------------- | --------------------------------------------------------- |
| pattern_name       | string           | Majority vote across N samples                            |
| pattern_confidence | float            | Mean confidence of samples that voted for winning pattern |
| size_cm            | float            | Median of N size measurements                             |
| mask               | np.ndarray       | Mask from the run closest to median size                  |
| color_proportions  | Dict[str, float] | K-Means on mask pixels (run once on selected mask)        |
| symmetry_score     | float            | Run once on selected mask                                 |

---

### 5. AppraisalResponse (updated Pydantic schema)

The API response returned to the frontend. This is the **updated** version replacing the current schema.

| Field              | Type             | Constraints      | Description                                      |
| ------------------ | ---------------- | ---------------- | ------------------------------------------------ |
| size_cm            | float            | ≥ 0              | Fish size in centimeters (median of N samples)   |
| pattern_name       | string           | non-empty        | Detected pattern (majority vote)                 |
| pattern_confidence | float            | 0.0–1.0          | Confidence score (mean of winning pattern votes) |
| color_proportions  | Dict[str, float] | values 0.0–100.0 | Named color → percentage mapping                 |
| symmetry_score     | float            | 0.0–1.0          | Bilateral symmetry score                         |

**Removed fields** (vs. current schema):

- `color_white_pct` — replaced by `color_proportions["White"]`
- `color_red_pct` — replaced by `color_proportions["Red"]`
- `color_black_pct` — replaced by `color_proportions["Black"]`
- `color_quality_score` — no equivalent in new approach
- `predicted_price` — feature removed entirely

---

### 6. AppraisalResult (updated TypeScript interface)

Frontend mirror of `AppraisalResponse`.

```typescript
export interface AppraisalResult {
  size_cm: number;
  pattern_name: string;
  pattern_confidence: number;
  color_proportions: Record<string, number>;
  symmetry_score: number;
}
```

**Removed fields**: `color_white_pct`, `color_red_pct`, `color_black_pct`, `color_quality_score`, `predicted_price`.

---

## Configuration Constants (new in config.py)

| Constant                 | Type             | Default | Description                                     |
| ------------------------ | ---------------- | ------- | ----------------------------------------------- |
| DEFAULT_K_CLUSTERS       | int              | 4       | Number of K-Means clusters (FR-002)             |
| COLOR_DISTANCE_THRESHOLD | float            | 50.0    | Max LAB distance for color name mapping         |
| DEFAULT_N_SAMPLES        | int              | 3       | Number of inference samples (FR-009)            |
| KMEANS_RANDOM_SEED       | int              | 42      | Fixed seed for reproducible clustering (SC-002) |
| KOI_COLOR_MAP            | Dict[str, tuple] | (table) | Named color → (L, a, b) mapping                 |

---

## State Transitions

### Appraisal Pipeline (updated flow)

```
Image Upload
  → [1] Generate N augmented variants (or 1 if n_samples=1)
  → [2] Run segmentation + coin detection on each variant → N (mask, size_cm) pairs
  → [3] Aggregate sizes via median → select representative mask
  → [4] Run pattern classification on each variant → N (name, confidence) pairs
  → [5] Aggregate patterns via majority vote → (name, mean_confidence)
  → [6] Run K-Means color analysis on representative mask → color_proportions
  → [7] Run symmetry analysis on representative mask → symmetry_score
  → [8] Construct AppraisalResponse
```

**Key difference from current flow**: Steps 1-5 are new (multi-sample). Steps 6-7 replace the old color analysis. Price prediction (old Step 5) is removed entirely.

---

## Entities Removed

| Entity                     | Reason                                     |
| -------------------------- | ------------------------------------------ |
| `ColorMetrics` (Pydantic)  | Replaced by `Dict[str, float]` proportions |
| `PricePredictor` class     | Price prediction feature removed (FR-005)  |
| `KoiPatternTrainer` class  | Training tied to price prediction, removed |
| `TrainingRequest` schema   | Training endpoint removed                  |
| `TrainingResponse` schema  | Training endpoint removed                  |
| `PatternTrainingConfig`    | Training endpoint removed                  |
| `PatternTrainingMetrics`   | Training endpoint removed                  |
| `ColorAnalyzer` (HSV)      | Replaced by new LAB K-Means analyzer       |
| `DEFAULT_COLOR_THRESHOLDS` | HSV thresholds no longer used              |
