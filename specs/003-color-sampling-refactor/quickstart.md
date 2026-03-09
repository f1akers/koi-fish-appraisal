# Quickstart: Color & Sampling Refactor

**Branch**: `003-color-sampling-refactor`
**Date**: 2026-03-09

---

## Overview

This feature makes three changes to the koi appraisal system:

1. **Color analysis rewrite** — Replace HSV thresholds with K-Means clustering in CIELAB colorspace
2. **Price prediction removal** — Strip all price estimation from backend and frontend
3. **Multi-sample aggregation** — Run ML models multiple times per image and aggregate results

The work is split into **two implementation sessions**:

- **Session 1 (Backend)**: Color service rewrite, price removal, multi-sample logic, schema/config/test updates
- **Session 2 (Frontend)**: Type updates, UI redesign, CSV export, price UI removal

---

## Session 1: Backend Changes

### Task order

1. **Remove price prediction** (FR-005)
   - Delete `backend/app/services/price_prediction.py`
   - Delete `backend/app/services/color_calibration_ui.py`
   - Delete `backend/app/train.py`
   - Remove `linear_*` entries from `MODEL_PATHS` in `config.py`
   - Remove `/train` endpoint and price logic from `routers/appraisal.py`
   - Remove training schemas from `schemas/appraisal.py`
   - Delete model files: `linear_*.json`, `linear_*.pkl`

2. **Update schemas** (FR-004, FR-011)
   - Replace fixed color fields with `color_proportions: Dict[str, float]` in `AppraisalResponse`
   - Remove `ColorMetrics`, `predicted_price`, `color_quality_score`
   - Add example with new shape

3. **Add color/sampling config** (FR-002, FR-009)
   - Add `DEFAULT_K_CLUSTERS`, `COLOR_DISTANCE_THRESHOLD`, `DEFAULT_N_SAMPLES`, `KMEANS_RANDOM_SEED` to `config.py`
   - Add `KOI_COLOR_MAP` static lookup table

4. **Rewrite color analysis service** (FR-001, FR-002, FR-003, FR-014)
   - Replace `ColorAnalyzer` class with LAB K-Means implementation
   - BGR → LAB conversion, mask pixel extraction, clustering, centroid-to-name mapping
   - "Other" fallback for unmapped centroids

5. **Add multi-sample aggregation** (FR-007, FR-008, FR-009, FR-010)
   - Add image augmentation utility (brightness jitter, rotation, flip)
   - Add pattern aggregation (majority vote + mean confidence)
   - Add size aggregation (median + representative mask selection)
   - Integrate into `routers/appraisal.py` pipeline

6. **Update router** (FR-004, FR-011)
   - Wire new color analysis and multi-sample aggregation into `/appraise`
   - Construct `AppraisalResponse` with new fields

7. **Update tests** (Constitution IV)
   - Update `test_appraisal.py` for new response schema
   - Add test for color proportions summing to ~100%
   - Add test for multi-sample aggregation with n_samples=1

### Verification

```bash
cd backend
pytest
```

All tests pass. API returns `color_proportions` dict, no `predicted_price`.

---

## Session 2: Frontend Changes

### Task order

1. **Update TypeScript types** (FR-006, FR-012)
   - Update `AppraisalResult` interface: add `color_proportions`, remove price/color fixed fields
   - Remove `ColorMetrics`, training-related types
   - Remove `PatternTrainingMetrics`, `TrainingResponse`, `TrainingRequest`, `PatternTrainingConfig`

2. **Update API service** (FR-006)
   - Remove `triggerTraining()` function from `api.ts`
   - Remove training type imports

3. **Redesign ResultsPanel** (FR-006, User Story 4)
   - Remove price hero card (the gradient violet card with "Estimated Value")
   - Remove "Color Quality" metric card
   - Keep: Size, Pattern, Symmetry metric cards
   - Keep: Color Distribution section (now with dynamic colors)

4. **Update ColorDistribution component** (User Story 4)
   - Accept `Record<string, number>` instead of fixed `white/red/black` props
   - Render dynamic color bars for each named color
   - Add color-to-CSS mapping for visual representation

5. **Update CSV export** (FR-013)
   - Remove `predicted_price`, `color_quality` columns
   - Replace fixed color columns with dynamic color proportion columns
   - Handle variable number of color columns

6. **Update App.tsx** (cosmetic)
   - Change tagline from "AI-Powered Fish Valuation" to "AI-Powered Fish Assessment" (or similar)

### Verification

```bash
cd frontend
npm run lint
npm run build
```

Zero lint errors, build succeeds, no price UI visible.

---

## Key Files Changed (by session)

### Session 1 (Backend)

| File                                   | Change                                                  |
| -------------------------------------- | ------------------------------------------------------- |
| `app/services/price_prediction.py`     | **DELETE**                                              |
| `app/services/color_calibration_ui.py` | **DELETE**                                              |
| `app/train.py`                         | **DELETE**                                              |
| `app/config.py`                        | Remove linear model paths, add color/sampling constants |
| `app/schemas/appraisal.py`             | New response schema, remove training schemas            |
| `app/services/color_analysis.py`       | **REWRITE** — LAB K-Means                               |
| `app/services/pattern_detection.py`    | Add multi-sample wrapper                                |
| `app/services/size_detection.py`       | Add multi-sample wrapper                                |
| `app/routers/appraisal.py`             | Remove price/training, add multi-sample pipeline        |
| `tests/test_appraisal.py`              | Update for new schema                                   |
| `models/linear_*.json`                 | **DELETE**                                              |

### Session 2 (Frontend)

| File                                   | Change                                          |
| -------------------------------------- | ----------------------------------------------- |
| `src/types/index.ts`                   | Update `AppraisalResult`, remove training types |
| `src/services/api.ts`                  | Remove `triggerTraining()`                      |
| `src/components/ResultsPanel.tsx`      | Remove price hero card                          |
| `src/components/ColorDistribution.tsx` | Dynamic color props                             |
| `src/utils/exportCsv.ts`               | Remove price column, dynamic colors             |
| `src/App.tsx`                          | Update tagline                                  |
