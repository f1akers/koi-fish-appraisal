# Tasks: Color & Sampling Refactor

**Input**: Design documents from `/specs/003-color-sampling-refactor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/appraise-endpoint.md, quickstart.md

**Tests**: Not explicitly requested — test tasks included only for updating existing tests to match new schema.

**Organization**: Tasks follow the **two-session plan** (Session 1: Backend, Session 2: Frontend) from plan.md, with phases organized by user story within each session.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/app/`, `backend/models/`, `backend/tests/`
- **Frontend**: `frontend/src/`

---

# SESSION 1: BACKEND

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Update configuration constants and remove deprecated model artifacts before any feature work begins.

- [x] T001 Update backend/app/config.py — remove `linear_ogon`, `linear_sanke`, `linear_kohaku` entries from `MODEL_PATHS`; add `DEFAULT_K_CLUSTERS = 4`, `COLOR_DISTANCE_THRESHOLD = 50.0`, `DEFAULT_N_SAMPLES = 3`, `KMEANS_RANDOM_SEED = 42`, and `KOI_COLOR_MAP` static LAB centroid lookup table (per data-model.md KoiColorMapEntry values)
- [x] T002 [P] Delete deprecated model files from backend/models/ — remove linear.json, linear.pkl, linear_kohaku.json, linear_kohaku.pkl, linear_ogon.json, linear_ogon.pkl, linear_sanke.json, linear_sanke.pkl

---

## Phase 2: Foundational — Price Removal & Schema Cleanup (Blocking)

**Purpose**: Remove all price prediction functionality and update schemas to the new response format. This phase MUST complete before any user story implementation.

**⚠️ CRITICAL**: The schema changes here define the new `AppraisalResponse` contract that all subsequent phases depend on.

- [x] T003 [P] Delete backend/app/services/price_prediction.py entirely (removes `PricePredictor` class and `predict_koi_price()`)
- [x] T004 [P] Delete backend/app/services/color_calibration_ui.py entirely (removes Tkinter HSV calibration UI, no longer needed with LAB approach)
- [x] T005 [P] Delete backend/app/train.py entirely (removes `KoiPatternTrainer` class and CLI entrypoint tied to price model training)
- [x] T006 Update backend/app/schemas/appraisal.py — remove `ColorMetrics` class, `TrainingRequest`, `TrainingResponse`, `PatternTrainingConfig`, `PatternTrainingMetrics` models; remove `color_white_pct`, `color_red_pct`, `color_black_pct`, `color_quality_score`, `predicted_price` fields from `AppraisalResponse`; add `color_proportions: Dict[str, float]` field to `AppraisalResponse`; update `json_schema_extra` example to match new contract from contracts/appraise-endpoint.md
- [x] T007 Update backend/app/routers/appraisal.py — remove `/train` endpoint (`trigger_training` function, ~50 lines), remove training schema imports (`TrainingRequest`, `TrainingResponse`, `PatternTrainingMetrics`), remove `price_prediction` service import, remove price prediction step from `/appraise` handler, update `AppraisalResponse` construction to use new schema fields, update `/model-status` to only report YOLO model paths (remove linear model entries)

**Checkpoint**: Backend compiles with updated schema. No price references remain. `/appraise` endpoint returns the new `AppraisalResponse` shape (color_proportions will be wired in Phase 3).

---

## Phase 3: User Story 1 — Accurate Color Distribution via Palette Clustering (P1) 🎯 MVP

**Goal**: Replace HSV threshold-based color analysis with K-Means clustering in CIELAB colorspace. Returns named color proportions (e.g., `{"Red": 42.3, "White": 35.1, "Black": 22.6}`).

**Independent Test**: Upload a koi fish image to `/api/appraise` and verify `color_proportions` contains named colors summing to ~100%.

### Implementation for User Story 1

- [x] T008 [US1] Rewrite backend/app/services/color_analysis.py — replace `ColorAnalyzer` class with new implementation: extract masked fish pixels via `mask > 0`, convert BGR→LAB with `cv2.cvtColor(image, cv2.COLOR_BGR2Lab)`, reshape to `(N, 3)` float64 array, cluster with `sklearn.cluster.KMeans(n_clusters=k, random_state=42, n_init=1)`, map cluster centroids to named koi colors using `KOI_COLOR_MAP` from config.py via Euclidean distance (threshold `COLOR_DISTANCE_THRESHOLD` for "Other" fallback), merge duplicate color mappings, return `Dict[str, float]` proportions summing to ~100%; keep module-level convenience function `analyze_fish_colors()` with updated signature; add edge case handling for few pixels (< 10 → warning log + single-cluster fallback); use logger (no bare print)
- [x] T009 [US1] Wire new color analysis into `/appraise` endpoint in backend/app/routers/appraisal.py — call updated `analyze_fish_colors()` with image and mask, assign result to `color_proportions` field of `AppraisalResponse`

**Checkpoint**: `/api/appraise` returns `color_proportions` with named koi colors. Single-pass pipeline works end-to-end.

---

## Phase 4: User Story 3 — Multi-Sample Aggregation for Reliable Results (P2)

**Goal**: Run pattern and size detection multiple times per image with input-level augmentation, aggregate via majority vote (pattern) and median (size) for more reliable results.

**Independent Test**: Submit the same image and verify aggregated result is at least as consistent as single-pass. Set `n_samples=1` and confirm identical behavior to single-pass.

### Implementation for User Story 3

- [x] T010 [US3] Add image augmentation utility function `augment_image(image, seed)` in backend/app/services/pattern_detection.py — implement mild brightness/contrast jitter (±10%), small rotation (±5°), 50% horizontal flip using cv2 and numpy RNG; seed=0 returns original unaugmented image (per research.md)
- [x] T011 [P] [US3] Add multi-sample pattern aggregation function in backend/app/services/pattern_detection.py — accept image + n_samples, generate augmented variants, run pattern classification on each, aggregate via majority vote for pattern name and mean confidence of winning votes; handle ties by highest mean confidence; return (pattern_name, pattern_confidence)
- [x] T012 [P] [US3] Add multi-sample size aggregation function in backend/app/services/size_detection.py — accept image + n_samples, generate augmented variants, run segmentation + coin detection on each, aggregate size via `np.median()`, select representative mask from run closest to median size; return (size_cm, representative_mask); coin detection runs once only (per research.md)
- [x] T013 [US3] Integrate multi-sample pipeline into `/appraise` endpoint in backend/app/routers/appraisal.py — replace single-pass pattern and size detection calls with multi-sample wrappers from T011/T012, pass `DEFAULT_N_SAMPLES` from config; run color analysis and symmetry on the representative mask from size aggregation; keep n_samples=1 backward-compatible (FR-010)

**Checkpoint**: `/api/appraise` runs multi-sample aggregation by default (n=3). Produces aggregated pattern (majority vote), size (median), and uses representative mask for color/symmetry.

---

## Phase 5: Backend Verification

**Purpose**: Update existing tests and verify the complete backend pipeline.

- [x] T014 Update backend/tests/test_appraisal.py — remove assertions on `predicted_price`, `color_white_pct`, `color_red_pct`, `color_black_pct`, `color_quality_score`; remove any `/train` endpoint tests; add assertions for `color_proportions` (dict type, values 0–100, sum ~100%); add assertion for `pattern_name`, `pattern_confidence`, `size_cm`, `symmetry_score` in new response shape; add test that n_samples=1 produces valid response
- [ ] T015 Run `cd backend && pytest` to verify all backend tests pass

**Checkpoint**: All backend tests green. Session 1 complete. API produces new response format per contracts/appraise-endpoint.md.

---

# SESSION 2: FRONTEND

---

## Phase 6: User Story 2 + User Story 4 — Frontend Price Removal & Criteria-Only Display (P1/P2)

**Goal**: Remove all price and training UI from the frontend. Display only four criteria: Size, Pattern, Color Distribution (dynamic named colors), and Symmetry.

**Independent Test**: Perform an appraisal and confirm: no price card/text visible, four criteria sections displayed, color distribution shows dynamic named color bars, CSV export has no price column.

### Implementation

- [x] T016 [P] [US2] Update frontend/src/types/index.ts — remove `ColorMetrics` interface, `PatternTrainingMetrics` interface, `TrainingResponse` interface, `PatternTrainingConfig` interface, `TrainingRequest` interface; update `AppraisalResult` interface to remove `color_white_pct`, `color_red_pct`, `color_black_pct`, `color_quality_score`, `predicted_price` and add `color_proportions: Record<string, number>`; update `AppraisalHistoryItem` if it references removed fields
- [x] T017 [P] [US2] Update frontend/src/services/api.ts — remove `triggerTraining()` function and its `TrainingRequest`/`TrainingResponse` type imports
- [x] T018 [US4] Redesign frontend/src/components/ResultsPanel.tsx — remove `formatPrice` function, remove "Price Hero Card" gradient div and all price display elements, remove "Color Quality" MetricCard; keep Size MetricCard, Pattern MetricCard (name + confidence), Symmetry MetricCard; keep ColorDistribution component (will receive new props in T019)
- [x] T019 [US4] Update frontend/src/components/ColorDistribution.tsx — change props from fixed `white_pct/red_pct/black_pct` to accept `colorProportions: Record<string, number>`; render dynamic named color bars for each entry (e.g., "Red: 42%", "White: 35%"); add color-name-to-CSS-color mapping (Red→#DC2626, White→#F5F5F4, Black→#171717, Orange→#EA580C, Yellow→#EAB308, Other→#9CA3AF)
- [x] T020 [P] [US2] Update frontend/src/utils/exportCsv.ts — remove `predicted_price` column, remove `color_quality` column, replace fixed `color_white_pct/color_red_pct/color_black_pct` columns with dynamic color proportion columns from `color_proportions` keys
- [x] T021 [P] Update frontend/src/App.tsx — change tagline from "AI-Powered Fish Valuation" to "AI-Powered Fish Assessment" on line 81

**Checkpoint**: Frontend displays criteria-only results. No price UI visible. Dynamic color distribution renders correctly.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and end-to-end validation.

- [x] T022 [P] Update frontend/src/components/index.ts if component export signatures changed (verify barrel exports still work)
- [x] T023 [P] Update docs/FEATURES_INDEX.md to reflect color analysis rewrite and price removal
- [x] T024 [P] Update docs/features/fish-metrics.md to document new color_proportions output format and multi-sample aggregation
- [x] T025 Run frontend lint and build verification — `cd frontend && npm run lint && npm run build`
- [x] T026 Run quickstart.md end-to-end validation — start backend (uvicorn), start frontend (vite), submit a koi image, verify response matches contracts/appraise-endpoint.md schema, verify UI shows 4 criteria sections with no price elements

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1 Color)**: Depends on Phase 2 — can start after schema is clean
- **Phase 4 (US3 Multi-Sample)**: Depends on Phase 3 — builds on working single-pass color pipeline
- **Phase 5 (Backend Tests)**: Depends on Phase 4 — validates complete backend
- **Phase 6 (US2+US4 Frontend)**: Depends on Phase 5 — frontend aligns with finalized API
- **Phase 7 (Polish)**: Depends on Phase 6 — final validation

### Session Boundaries

- **Session 1 (Backend)**: Phases 1–5 (T001–T015)
- **Session 2 (Frontend)**: Phases 6–7 (T016–T026)
- Sessions are designed to be implemented sequentially, with Session 1 producing a working API before Session 2 starts

### Within Each Phase

- Tasks marked [P] within a phase can run in parallel
- Non-[P] tasks should run sequentially in listed order
- File deletions (T002–T005) are always safe to parallelize

### Parallel Opportunities

**Phase 1**: T001 and T002 are parallel (config file vs model file deletions)

**Phase 2**: T003, T004, T005 are parallel (independent file deletions); T006 and T007 are sequential (schema before router)

**Phase 3**: T008 then T009 (service before router wiring)

**Phase 4**: T010 first (augmentation utility), then T011 and T012 in parallel (pattern vs size wrappers in different files), then T013 (router integration)

**Phase 6**: T016, T017, T020, T021 are parallel (different files); T018 depends on T016 (types); T019 depends on T018 (ResultsPanel before ColorDistribution for prop changes)

---

## Parallel Example: Phase 2 (Foundational)

```
# Parallel file deletions:
Task T003: "Delete backend/app/services/price_prediction.py"
Task T004: "Delete backend/app/services/color_calibration_ui.py"
Task T005: "Delete backend/app/train.py"

# Sequential schema/router updates (after deletions):
Task T006: "Update schemas/appraisal.py"
Task T007: "Update routers/appraisal.py"
```

## Parallel Example: Phase 4 (Multi-Sample)

```
# First: augmentation utility
Task T010: "Add augment_image() in pattern_detection.py"

# Then parallel wrappers:
Task T011: "Multi-sample pattern aggregation in pattern_detection.py"
Task T012: "Multi-sample size aggregation in size_detection.py"

# Finally: router integration
Task T013: "Integrate multi-sample pipeline in routers/appraisal.py"
```

## Parallel Example: Phase 6 (Frontend)

```
# Parallel independent file updates:
Task T016: "Update types/index.ts"
Task T017: "Update services/api.ts"
Task T020: "Update utils/exportCsv.ts"
Task T021: "Update App.tsx tagline"

# Sequential after T016:
Task T018: "Redesign ResultsPanel.tsx"
Task T019: "Update ColorDistribution.tsx"
```

---

## Implementation Strategy

### MVP First (Session 1 Only)

1. Complete Phase 1: Setup (config + cleanup)
2. Complete Phase 2: Foundational (price removal + schema)
3. Complete Phase 3: User Story 1 (color analysis rewrite)
4. **STOP and VALIDATE**: API returns `color_proportions` — test independently
5. Continue to Phase 4: User Story 3 (multi-sample aggregation)
6. Complete Phase 5: Backend tests pass
7. **Session 1 complete** — backend API is production-ready with new contract

### Incremental Delivery

1. Setup + Foundational → Price removed, schema clean
2. US1 (Color) → New color analysis working end-to-end (MVP!)
3. US3 (Multi-Sample) → Enhanced reliability via aggregation
4. Backend tests → Session 1 verified
5. US2+US4 (Frontend) → UI aligned with new API
6. Polish → Docs updated, full E2E validated

### Two-Session Benefits

- **Session 1** can be completed, tested, and committed independently
- **Session 2** only starts when the API contract is finalized
- Rollback boundary: if Session 2 has issues, Session 1 API still works (e.g., via curl/Postman)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [US*] labels map tasks to spec.md user stories for traceability
- US2 (Price Removal) spans both sessions: backend in Phase 2, frontend in Phase 6
- US4 (Frontend Criteria-Only) is entirely in Phase 6
- Commit after each phase or logical group
- Stop at any checkpoint to validate independently
- Performance budget: 15s for 3 inference samples (SC-005)
- Color proportions must sum to ~100% (±1% tolerance per SC-001)
- K-Means seeded with `random_state=42` for reproducibility (SC-002)
