# Phase 0 Research: Color & Sampling Refactor

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Date**: 2026-03-09  
**Status**: Complete

---

## Topic 1: K-Means in CIELAB Colorspace Best Practices

### Decision

Use `cv2.cvtColor(image, cv2.COLOR_BGR2Lab)` to convert the masked fish pixels from BGR to CIELAB, reshape the pixel data to a 2D array of shape `(N, 3)`, cast to `float64`, and cluster with `sklearn.cluster.KMeans(n_clusters=k, random_state=42, n_init=1)`. Default `k=4`. No normalization of LAB channels is needed because Euclidean distance in CIELAB is already perceptually meaningful.

### Rationale

**BGR → CIELAB conversion.** OpenCV loads images in BGR. The conversion is a single call:

```python
lab_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2Lab)
```

OpenCV's CIELAB implementation uses the D65 illuminant. The output ranges are L\* ∈ [0, 255] (mapped from 0–100), a\* ∈ [0, 255] (offset from −128 to +127), b\* ∈ [0, 255] (offset from −128 to +127) for `uint8` input. This is fine for clustering; the offset/scale is consistent across all pixels so relative distances are preserved.

**Reshaping.** The masked fish pixels must be extracted and reshaped to `(N, 3)` for scikit-learn:

```python
# Extract only fish pixels using the binary mask
fish_pixels = lab_image[mask > 0]  # shape: (N, 3)
fish_pixels = fish_pixels.astype(np.float64)
```

This automatically excludes background pixels (FR-003). No further normalization (e.g., StandardScaler) is needed because CIELAB channels are already on comparable scales and Euclidean distance in LAB is designed to be perceptually uniform.

**Reproducibility.** `random_state=42` seeds the centroid initialization. Setting `n_init=1` ensures only a single initialization run occurs, making the result fully deterministic for the same input (SC-002). With `n_init > 1`, scikit-learn runs multiple initializations and picks the best — this produces the same final result for the same `random_state`, but is slower and unnecessary when determinism with a fixed seed is the goal.

**Cluster count (k).** Koi fish typically show 2–3 dominant colors (e.g., Kohaku: red+white, Sanke: red+white+black, Ogon: single gold). A default of `k=4` provides enough resolution to capture the primary colors plus a secondary/transition color, without over-segmenting. The spec allows `k` to be configurable in the range 3–5 (FR-002).

### Alternatives Considered

| Alternative                                                  | Why Rejected                                                                                                                                                                                                               |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Normalize LAB channels with StandardScaler**               | CIELAB is already perceptually uniform. Normalizing would distort the perceptual distance metric that makes LAB valuable.                                                                                                  |
| **Use HSV or RGB for clustering**                            | HSV has hue wraparound issues (red spans 0° and 360°). RGB Euclidean distance does not correlate well with perceived color difference. LAB is the standard for perceptual color work.                                      |
| **`n_init=10` (scikit-learn default)**                       | Produces the same final result for a given `random_state` but takes 10× longer. Since we fix the seed and want determinism + speed, `n_init=1` is sufficient.                                                              |
| **k=3 default**                                              | Insufficient for Sanke (3 colors + potential transition shades). k=4 is a better general-purpose default.                                                                                                                  |
| **k=5 default**                                              | Over-segments for simpler patterns like Ogon. k=4 is the sweet spot; users can configure up.                                                                                                                               |
| **MiniBatchKMeans**                                          | Faster on very large datasets, but a single koi mask is typically 50K–500K pixels — standard KMeans handles this in <1 second. Not worth the API complexity.                                                               |
| **Convert to float LAB (0–100, −128–127) before clustering** | Would require manual conversion from OpenCV's uint8 LAB encoding. Unnecessary because distances are proportionally equivalent in either encoding, and the centroid-to-color mapping table can use the same uint8 encoding. |

---

## Topic 2: Mapping LAB Cluster Centroids to Named Koi Colors

### Decision

Define a static lookup table of named koi colors with their CIELAB centroid values (in OpenCV's uint8 encoding). For each K-Means cluster centroid, compute Euclidean distance to all named colors and assign the nearest one. If the nearest distance exceeds a threshold of **50.0** (in uint8 LAB space, roughly equivalent to ΔE ≈ 20 in standard CIELAB), classify the cluster as "Other". If two clusters map to the same named color, merge their proportions.

### Rationale

**Reference CIELAB values for koi colors.** These values are in OpenCV's uint8 LAB encoding (L: 0–255, a: 0–255 offset by 128, b: 0–255 offset by 128):

| Koi Color              | L\* | a\* | b\* | Notes                                                |
| ---------------------- | --- | --- | --- | ---------------------------------------------------- |
| **White** (Shiroji)    | 245 | 128 | 128 | Near-neutral, very high lightness                    |
| **Red** (Hi)           | 140 | 185 | 175 | High a\* (red), moderate b\* (warm)                  |
| **Black** (Sumi)       | 30  | 128 | 128 | Near-neutral, very low lightness                     |
| **Orange** (Beni-like) | 175 | 170 | 190 | Moderate-high L\*, positive a\* and b\*              |
| **Yellow** (Ki)        | 220 | 118 | 200 | High L\*, slightly negative a\*, strong positive b\* |

These values are derived from typical koi coloration photographed under daylight. They serve as starting reference points and may be tuned based on sample images.

**Euclidean distance in LAB.** CIELAB was designed so that Euclidean distance between two points approximates perceptual color difference (ΔE\*ab). In OpenCV's uint8 encoding, the scaling is linear — a distance of ~2.55 uint8 units ≈ 1 ΔE unit. A threshold of 50 uint8 units ≈ ΔE 20, which is a generous "same general color" boundary. Colors with ΔE > 20 are unambiguously different colors to the human eye.

**"Other" fallback.** When a centroid is farther than the threshold from all named colors, it's classified as "Other" (FR-014). This handles transition zones, unusual colors (e.g., metallic sheens), or segmentation artifacts. The "Other" proportion is reported normally.

**Duplicate mapping.** If two clusters both map to "Red", their proportions are summed. This is straightforward and expected when k > number of distinct colors present.

### Alternatives Considered

| Alternative                                              | Why Rejected                                                                                                                                                                                                                                       |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CIEDE2000 distance**                                   | More perceptually accurate than simple Euclidean in LAB, but significantly more complex to implement. The improvement is marginal for the coarse color categories used here (5 named colors + Other). Euclidean ΔE\*ab is standard and sufficient. |
| **No distance threshold (always assign nearest)**        | Could produce misleading labels. A metallic gold centroid equidistant from Yellow and Orange might be labeled one or the other unpredictably. "Other" is a safer default for ambiguous cases.                                                      |
| **Dynamic threshold per color**                          | Adds complexity without clear benefit. The named koi colors are spread far apart in LAB space, so a single threshold works for all.                                                                                                                |
| **Use a trained classifier instead of nearest-centroid** | Over-engineered for 5 fixed color classes. A classifier would need training data per color, which we don't have. Nearest-centroid lookup is simple, fast, and interpretable.                                                                       |
| **HSV-based color naming**                               | The existing system already uses HSV and is being replaced specifically because of hue wraparound issues (red) and lighting sensitivity. LAB avoids both.                                                                                          |
| **Threshold of 30 (stricter)**                           | Would classify too many legitimate koi colors as "Other", especially when lighting shifts centroid positions slightly. 50 provides a reasonable buffer.                                                                                            |
| **Threshold of 80 (looser)**                             | Would rarely trigger "Other", potentially misclassifying very different colors. 50 is a balanced middle ground.                                                                                                                                    |

---

## Topic 3: Multi-Sample Aggregation for YOLO Inference

### Decision

Use input-level augmentation (slight brightness/contrast jitter, minor rotation ≤5°, horizontal flip) to generate variant images from the single upload, then run each variant through the YOLO model independently. Aggregate pattern classification via **majority vote** (pattern name) with **mean confidence**. Aggregate size/segmentation via **median** of size measurements. Default sample count: **3**.

Do **not** use Ultralytics' built-in `augment=True` (test-time augmentation / TTA).

### Rationale

**Why augmentation is needed.** YOLOv8 inference is deterministic for identical input (same weights, same image, same hardware). To get meaningful variation across samples, the input image must differ between runs. Small augmentations simulate the natural variation between multiple real photos of the same fish.

**Why not Ultralytics TTA (`augment=True`).** Ultralytics YOLOv8 does support `augment=True` in the `model.predict()` call, which applies test-time augmentation (multi-scale inference with flips). However:

1. TTA is designed for **detection/segmentation accuracy improvement**, not for producing multiple distinct result sets to aggregate. It returns a single merged result, not N separate results.
2. TTA roughly **3× the inference time** for a single call and cannot be customized (the augmentations are hardcoded: scale variations + horizontal flip).
3. Our goal is to produce **N independent result sets** that we can aggregate with majority vote / median — this requires N separate inference calls on N augmented inputs.

**Augmentation strategy.** Keep augmentations mild to avoid changing the image semantics:

```python
def augment_image(image: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # Brightness/contrast jitter: ±10%
    alpha = rng.uniform(0.9, 1.1)  # contrast
    beta = rng.uniform(-10, 10)     # brightness
    augmented = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    # Small rotation: ±5 degrees
    angle = rng.uniform(-5, 5)
    h, w = augmented.shape[:2]
    M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
    augmented = cv2.warpAffine(augmented, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    # Optional horizontal flip (50% chance)
    if rng.random() > 0.5:
        augmented = cv2.flip(augmented, 1)
    return augmented
```

Pass `seed=0` corresponds to the original (unaugmented) image to ensure one sample is always the clean input.

**Pattern aggregation (majority vote + mean confidence).** Collect `[(pattern_name, confidence), ...]` from N runs. The pattern name appearing most often is selected. The confidence is the mean of all confidences for that winning pattern. If there's a tie, select the pattern with the highest mean confidence among tied candidates. This satisfies FR-007.

**Size aggregation (median).** Collect `[size_cm_1, size_cm_2, ..., size_cm_N]` from N runs. Use `np.median()` as the final size. Median is robust to outliers from occasional poor segmentation (edge case noted in spec). This satisfies FR-008.

**Mask aggregation.** For downstream color/symmetry analysis, use the mask from the **median-size run** (the run whose size measurement is closest to the median). This avoids needing to merge masks and provides a representative segmentation.

**Performance.** With 3 samples, inference time is approximately 3× single-pass. For YOLOv8 on a typical GPU:

- Segmentation: ~50–150ms per pass → ~150–450ms for 3 passes
- Classification: ~20–50ms per pass → ~60–150ms for 3 passes
- Coin detection: Run once only (coin doesn't benefit from augmentation)
- Color analysis (KMeans): Run once on the selected mask
- Total overhead: ~200–500ms additional for 3 samples

Well within the 15-second budget (SC-005). Most of the time budget is in model cold-start (first inference loads the model into memory), not per-image inference.

**Sample count of 1.** When `n_samples=1`, no augmentation is applied and the pipeline runs identically to single-pass (FR-010).

### Alternatives Considered

| Alternative                                            | Why Rejected                                                                                                                                                                           |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ultralytics `augment=True` (TTA)**                   | Returns a single merged result, not N independent results for aggregation. Cannot customize augmentation types. Designed for accuracy boost on a single pass, not multi-sample voting. |
| **Dropout-based uncertainty (MC Dropout)**             | Requires modifying the YOLO model to enable dropout at inference time. Not supported by Ultralytics without model surgery. Over-engineered for this use case.                          |
| **5 samples default**                                  | Diminishing returns beyond 3 for majority vote with 3 pattern classes. 5 samples would add ~300ms for marginal benefit. 3 is the minimum for a meaningful majority vote.               |
| **Mean for size aggregation**                          | Sensitive to outliers. A single bad segmentation could skew the average. Median is more robust.                                                                                        |
| **Run same image N times (no augmentation)**           | Produces identical results every time (YOLO is deterministic). No benefit from aggregation. Augmentation is required for meaningful variation.                                         |
| **Augment mask instead of image**                      | Mask comes from segmentation output, not input. Augmenting the input naturally produces different masks. Augmenting masks directly would be artificial.                                |
| **Heavy augmentation (large rotations, color shifts)** | Risk changing the image semantics enough to confuse the model. Mild augmentation (±5° rotation, ±10% brightness) is safer.                                                             |

---

## Topic 4: Removing Price Prediction — Impact Analysis

### Decision

Remove all price prediction functionality. This is a clean removal with no replacement functionality needed. The specific files, code sections, and model artifacts to remove/modify are enumerated below.

### Rationale

The spec explicitly calls for removing price prediction (FR-005, FR-006). The feature depends on trained linear regression models that require per-pattern training data with prices — data the project doesn't reliably have. Removing it simplifies the codebase, eliminates model file dependencies, and refocuses the tool on objective fish assessment criteria.

### Files to Remove Entirely

| File                                                                                               | Purpose                                                            | Safe to Delete                                                                                         |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| [backend/app/services/price_prediction.py](../../backend/app/services/price_prediction.py)         | `PricePredictor` class, `predict_koi_price()` convenience function | Yes — only imported by `routers/appraisal.py` (for `/appraise` and indirectly by `/train`)             |
| [backend/app/services/color_calibration_ui.py](../../backend/app/services/color_calibration_ui.py) | Tkinter HSV calibration UI                                         | Yes — standalone tool, not imported by any service or router. Tied to the HSV approach being replaced. |
| [backend/app/train.py](../../backend/app/train.py)                                                 | `KoiPatternTrainer` class, `train_all_patterns()`, CLI entrypoint  | Yes — only imported by `routers/appraisal.py` inside the `/train` endpoint handler.                    |
| `backend/models/linear.json`                                                                       | Legacy single-model metadata                                       | Yes — unused by current per-pattern code.                                                              |
| `backend/models/linear.pkl`                                                                        | Legacy single-model weights                                        | Yes — unused by current per-pattern code.                                                              |
| `backend/models/linear_ogon.json`                                                                  | Ogon model metadata                                                | Yes — used only by price prediction.                                                                   |
| `backend/models/linear_ogon.pkl`                                                                   | Ogon model weights                                                 | Yes — used only by price prediction.                                                                   |
| `backend/models/linear_sanke.json`                                                                 | Sanke model metadata                                               | Yes — used only by price prediction.                                                                   |
| `backend/models/linear_sanke.pkl`                                                                  | Sanke model weights                                                | Yes — used only by price prediction.                                                                   |
| `backend/models/linear_kohaku.json`                                                                | Kohaku model metadata                                              | Yes — used only by price prediction.                                                                   |
| `backend/models/linear_kohaku.pkl`                                                                 | Kohaku model weights                                               | Yes — used only by price prediction.                                                                   |

Also remove `backend/models/color_calibration.json` if it exists (HSV calibration data, replaced by LAB clustering).

### Router Changes (appraisal.py)

| Change                       | Details                                                                                                                                                                                                                                                   |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Remove imports**           | Remove `TrainingRequest`, `TrainingResponse`, `PatternTrainingMetrics` from schema imports. Remove `get_price_predictor` from service imports. Remove `KOI_PATTERNS` import (only used for price logic gating; re-check if still needed for other logic). |
| **Remove from `/appraise`**  | Remove the entire "Step 5: Price prediction" block (~20 lines). Remove `predicted_price` from the `AppraisalResponse` constructor.                                                                                                                        |
| **Remove `/train` endpoint** | Remove the entire `trigger_training()` function and its `@router.post("/train")` decorator (~50 lines).                                                                                                                                                   |
| **Keep `/model-status`**     | Update to only report YOLO model paths (remove `linear_*` entries that will no longer exist in `MODEL_PATHS`).                                                                                                                                            |

### Schema Changes (schemas/appraisal.py)

| Change                              | Details                                                                                                                                                              |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Remove `predicted_price`**        | Remove from `AppraisalResponse` and its example.                                                                                                                     |
| **Remove `color_quality_score`**    | Remove from `AppraisalResponse` — replaced by proportions (no single quality metric in new approach).                                                                |
| **Remove fixed color fields**       | Remove `color_white_pct`, `color_red_pct`, `color_black_pct` from `AppraisalResponse`. Replace with `color_proportions: Dict[str, float]` — dynamic named color map. |
| **Remove `ColorMetrics`**           | No longer needed — replaced by `Dict[str, float]` color proportions or a new `ColorProportions` model.                                                               |
| **Remove `TrainingRequest`**        | Entire model removed.                                                                                                                                                |
| **Remove `TrainingResponse`**       | Entire model removed.                                                                                                                                                |
| **Remove `PatternTrainingConfig`**  | Entire model removed.                                                                                                                                                |
| **Remove `PatternTrainingMetrics`** | Entire model removed.                                                                                                                                                |

### Config Changes (config.py)

| Change                        | Details                                                                                                                                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Remove from `MODEL_PATHS`** | Remove `linear_ogon`, `linear_sanke`, `linear_kohaku` entries.                                                                                                                                                            |
| **Add color/sampling config** | Add `DEFAULT_K_CLUSTERS = 4`, `COLOR_DISTANCE_THRESHOLD = 50.0`, `DEFAULT_N_SAMPLES = 3`, `KOI_COLOR_MAP` (LAB centroids dict). These can go in `config.py` or as module-level constants in the respective service files. |

### Dependency Impact

- **No new dependencies required.** `scikit-learn` (for KMeans) and `opencv-python` (for LAB conversion) are already in `requirements.txt`.
- **Dependencies that can be removed.** `pickle` usage in price_prediction.py goes away. The `sklearn.linear_model`, `sklearn.preprocessing.StandardScaler`, `sklearn.model_selection`, and `sklearn.metrics` imports in `train.py` go away. `scikit-learn` itself stays (used by KMeans).
- **No impact on YOLO models.** `koi-segment.pt`, `coin.pt`, `koi-pattern.pt` are unaffected.

### Test Impact (test_appraisal.py)

The existing test file must be updated to:

1. Remove any assertions on `predicted_price` in the appraisal response.
2. Remove any tests for the `/train` endpoint.
3. Update response shape assertions to expect `color_proportions` (dict) instead of `color_white_pct`, `color_red_pct`, `color_black_pct`, `color_quality_score`.
4. Add new tests for the color clustering output format.

### Alternatives Considered

| Alternative                                       | Why Rejected                                                                                                                                                                                                                                                      |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Keep price prediction as optional/disabled**    | Adds dead code complexity. The spec explicitly requires removal (FR-005). Keeping inactive code creates maintenance burden and confusion.                                                                                                                         |
| **Keep training endpoint for future use**         | The training endpoint is tightly coupled to price prediction. If price prediction is removed, the training endpoint has no purpose. Can be re-added later if needed.                                                                                              |
| **Keep `color_quality_score`**                    | The quality score was derived from HSV saturation, edge sharpness, and per-color consistency — all tied to the HSV threshold approach. The new LAB clustering approach doesn't produce an equivalent metric. Could be re-designed separately in a future feature. |
| **Keep `ColorMetrics` model with updated fields** | The fixed 3-color model (white/red/black percentages + quality) doesn't match the new dynamic color proportions output. A `Dict[str, float]` or new Pydantic model is cleaner.                                                                                    |

---

## Summary Table

| Topic                       | Key Decision                                                                                         | Confidence                                                                      |
| --------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 1. K-Means in LAB           | `cv2.COLOR_BGR2Lab` → reshape → `KMeans(n_clusters=4, random_state=42, n_init=1)`. No normalization. | High — standard practice, well-documented APIs                                  |
| 2. Color mapping            | Static LAB centroid table, Euclidean nearest-match, threshold=50 for "Other" fallback                | High — simple, interpretable, tunable                                           |
| 3. Multi-sample aggregation | Input augmentation (mild jitter/rotation), 3 samples, majority vote + median size. No TTA.           | High — TTA doesn't fit the multi-result aggregation model                       |
| 4. Price removal            | Clean removal of 3 service files, 6+ model files, training endpoint, price schema fields             | High — straightforward deletion, no entanglements beyond identified touchpoints |
