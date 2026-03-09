# Feature Specification: Color & Sampling Refactor

**Feature Branch**: `003-color-sampling-refactor`  
**Created**: 2026-03-09  
**Status**: Draft  
**Input**: User description: "Redo color estimation with palette-based K-Means clustering in LAB colorspace, remove price estimation, and add multi-sample aggregation for pattern and size detection"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Accurate Color Distribution via Palette Clustering (Priority: P1)

A koi hobbyist captures a photo of their fish. The system segments the fish from the background and analyzes its colors using palette-based clustering rather than fixed HSV thresholds. The user sees a breakdown of named color proportions (e.g., "42% Red, 35% White, 23% Black") that accurately reflects the visible colors on the fish, regardless of lighting variations.

**Why this priority**: Color analysis is the core metric being redesigned. The current HSV threshold approach is brittle under different lighting conditions. Palette-based clustering in LAB colorspace is more perceptually uniform and produces reliable, deterministic results without maintaining calibration files or model weights.

**Independent Test**: Can be fully tested by uploading a koi fish image and verifying the returned color proportions match a visual inspection of the fish. Delivers immediate value as a standalone improvement to color accuracy.

**Acceptance Scenarios**:

1. **Given** a captured koi fish image with a clear segmentation mask, **When** the system analyzes colors, **Then** it returns named color proportions (e.g., Red, White, Black, Orange) that sum to approximately 100%.
2. **Given** two photos of the same fish under slightly different lighting, **When** colors are analyzed for both, **Then** the proportions are within a reasonable tolerance of each other (more consistent than the previous HSV approach).
3. **Given** a segmented fish image, **When** color analysis runs, **Then** it uses K-Means clustering (k=3–5) in LAB colorspace and maps cluster centroids to named koi colors.
4. **Given** pixels outside the fish mask, **When** clustering is performed, **Then** those pixels are excluded from analysis.

---

### User Story 2 - Price Estimation Removed from Appraisal (Priority: P1)

A user captures a koi fish image. The system returns size, pattern, color distribution, and symmetry metrics only. No price prediction is shown. The frontend no longer displays the price hero card or any price-related information.

**Why this priority**: The price estimation feature is being intentionally removed. This is a scope reduction that simplifies the system, removes dependency on trained linear regression models, and refocuses the tool on objective fish criteria assessment.

**Independent Test**: Can be tested by performing an appraisal and confirming no price field appears in the API response or frontend display. The system should function fully without any price prediction model files.

**Acceptance Scenarios**:

1. **Given** a user submits a koi fish image for appraisal, **When** the backend processes it, **Then** the response contains size, pattern, color, and symmetry metrics but no price prediction field.
2. **Given** the frontend receives appraisal results, **When** it renders the results panel, **Then** no price card, price value, or price-related UI is displayed.
3. **Given** the backend starts up, **When** it initializes services, **Then** it does not attempt to load any linear regression price models.
4. **Given** a user exports results to CSV, **When** the export is generated, **Then** no price column is included.

---

### User Story 3 - Multi-Sample Aggregation for Reliable Results (Priority: P2)

A user captures a photo of their koi fish. The system takes the single uploaded image and runs multiple inference samples through the ML models (pattern classification and size/segment detection) to produce a more reliable aggregated result. Instead of relying on a single model pass, the system combines results from multiple runs to reduce variance and improve confidence.

**Why this priority**: Single-pass inference can produce noisy results, especially with varying image quality. Multi-sample aggregation provides a smoothing effect that reduces individual run anomalies. This builds on a working single-pass system (P1 stories) and enhances reliability.

**Independent Test**: Can be tested by submitting the same image and comparing the aggregated result against a single-pass result. The aggregated result should show equal or higher consistency across repeated submissions.

**Acceptance Scenarios**:

1. **Given** a koi fish image is submitted, **When** the system processes it, **Then** it runs the pattern detection model multiple times (configurable, default 3–5 samples) and returns the most frequently predicted pattern along with an averaged confidence score.
2. **Given** a koi fish image is submitted, **When** the system processes it, **Then** it runs the segmentation model multiple times and aggregates the size measurement (e.g., median or mean) to reduce single-run variance.
3. **Given** multi-sample aggregation is enabled, **When** the number of samples is set to 1, **Then** the system behaves identically to single-pass inference (backward compatible).
4. **Given** multiple inference runs produce differing pattern predictions, **When** results are aggregated, **Then** the majority-vote pattern is selected, and the confidence reflects the agreement level across samples.

---

### User Story 4 - Frontend Displays Criteria-Only Results (Priority: P2)

A user views appraisal results on the frontend. The interface displays only the objective criteria: size (cm), pattern (name + confidence), color distribution (named color proportions as percentages), and symmetry score. The layout is clean and focused on these four criteria without price or quality score cards.

**Why this priority**: The frontend must reflect the backend changes. Displaying only criteria keeps the user experience aligned with the new system scope and removes confusion from deprecated features.

**Independent Test**: Can be tested by performing an appraisal and visually confirming the results screen shows exactly the four criteria cards and color distribution chart with no price or quality score elements.

**Acceptance Scenarios**:

1. **Given** appraisal results are returned, **When** the results panel renders, **Then** it displays metric cards for Size, Pattern, Symmetry, and a Color Distribution section.
2. **Given** the color distribution section renders, **When** color data is available, **Then** it shows named color proportions with visual bars (e.g., "Red: 42%", "White: 35%", "Black: 23%") reflecting the new clustering output.
3. **Given** the frontend type definitions, **When** the `AppraisalResult` interface is used, **Then** it no longer includes `predicted_price` or `color_quality_score` fields.
4. **Given** the results panel, **When** rendered, **Then** no "Estimated Value" hero card or price-related text is visible.

---

### Edge Cases

- What happens when the segmentation mask contains very few pixels (e.g., tiny fish or poor segmentation)? The system should return a warning or fallback to a single-cluster analysis when pixel count is below a minimum threshold.
- What happens when K-Means produces a cluster that doesn't map to any known koi color? The system should classify it as "Other" with its proportion included.
- What happens when all multi-sample inference runs produce different pattern predictions (no clear majority)? The system should return the pattern with the highest average confidence across runs and flag the low agreement.
- What happens when the uploaded image has no detectable fish? The existing error handling should continue to return an appropriate error message.
- What happens when multi-sample aggregation for size detection produces an outlier in one run? Using median (rather than mean) mitigates outlier impact.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST replace the existing HSV threshold-based color analysis with a palette-based K-Means clustering approach operating in CIELAB colorspace.
- **FR-002**: System MUST cluster masked fish pixels into 3–5 clusters (configurable, default k=4) and map each cluster centroid to a named koi color (e.g., Red, White, Black, Orange, Yellow).
- **FR-003**: System MUST exclude masked-out (background) pixels from the clustering analysis.
- **FR-004**: System MUST return color results as a dictionary of named colors mapped to their proportion (percentage) of the total fish pixels.
- **FR-005**: System MUST remove all price prediction functionality from the backend, including the price prediction service, model loading, API response fields, and training endpoints related to price.
- **FR-006**: System MUST remove all price-related display elements from the frontend, including the price hero card, price formatting utilities, and price fields in TypeScript type definitions.
- **FR-007**: System MUST support running pattern detection inference multiple times per image and aggregating results via majority vote for pattern name and mean for confidence score.
- **FR-008**: System MUST support running segmentation/size detection inference multiple times per image and aggregating size measurements using median to reduce outlier impact.
- **FR-009**: The number of inference samples MUST be configurable with a sensible default (default: 3).
- **FR-010**: System MUST behave identically to single-pass when the sample count is set to 1.
- **FR-011**: System MUST update the API response schema to remove price fields and update color fields to support dynamic named color proportions.
- **FR-012**: System MUST update the frontend `AppraisalResult` types and components to align with the new API response schema.
- **FR-013**: System MUST update CSV export to exclude price data and include the new color proportion format.
- **FR-014**: The color name mapping MUST include at minimum: Red, White, Black, Orange, and Yellow, with an "Other" fallback for unmapped colors.

### Key Entities

- **Color Proportion**: A named koi color (e.g., Red, White, Black) paired with its percentage of total fish pixels. Replaces the previous fixed three-color percentage model.
- **Inference Sample**: A single run of an ML model (pattern or segmentation) on the same input image. Multiple samples are aggregated for a final result.
- **Aggregated Result**: The final combined output from multiple inference samples — majority-vote pattern, mean confidence, median size.
- **Koi Color Map**: A lookup table mapping LAB colorspace centroids to named koi colors. Used by the clustering step.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Color analysis produces named color proportions that sum to 100% (±1% rounding tolerance) for every valid fish image.
- **SC-002**: Color analysis results for the same image are fully deterministic when a fixed random seed is used for clustering.
- **SC-003**: No price-related data appears anywhere in the application — API responses, frontend UI, or CSV exports.
- **SC-004**: Multi-sample aggregation with 3+ samples produces pattern classification results that are at least as consistent as single-pass inference when tested across repeated submissions of the same image.
- **SC-005**: The appraisal workflow completes within a reasonable time for the user (under 15 seconds for a single image with 3 samples).
- **SC-006**: All existing appraisal functionality (size detection, pattern recognition, symmetry analysis) continues to work correctly after changes.
- **SC-007**: The frontend displays exactly four criteria sections (Size, Pattern, Color Distribution, Symmetry) with no price or quality score elements.

## Assumptions

- The existing koi segmentation model (`koi-segment.pt`) and pattern classification model (`koi-pattern.pt`) continue to work as-is; no retraining is needed.
- The coin reference-based size detection remains unchanged in its core logic; only the aggregation wrapper is new.
- scikit-learn's `KMeans` is already available as a project dependency (listed in requirements.txt) or will be added.
- A static koi color mapping table (LAB centroid to named color) is sufficient; no dynamic learning of color names is needed.
- The K-Means random seed will be fixed for reproducibility by default.
- The existing symmetry analysis service is unaffected by these changes.
- The linear regression trainer feature and its training endpoints may be removed or left inactive since price prediction is being dropped. Training scripts for price models are no longer needed.
- The "quality_score" for colors is removed since the new clustering approach produces proportions rather than a quality metric.
