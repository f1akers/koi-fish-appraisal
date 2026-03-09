# Implementation Plan: Color & Sampling Refactor

**Branch**: `003-color-sampling-refactor` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-color-sampling-refactor/spec.md`

## Summary

Replace HSV threshold-based color analysis with palette-based K-Means clustering in CIELAB colorspace, remove all price estimation functionality, and add multi-sample aggregation for pattern and size detection. The work is split into **two implementation sessions**: backend changes (Session 1) and frontend changes (Session 2).

## Technical Context

**Language/Version**: Python 3.10+ (backend), TypeScript strict (frontend)
**Primary Dependencies**: FastAPI, Pydantic v2, OpenCV, scikit-learn (KMeans), Ultralytics YOLOv8, React 19+, Vite 7+, Tailwind CSS 4+
**Storage**: File-based ML models in `backend/models/`, no database
**Testing**: pytest + FastAPI TestClient (backend), ESLint + tsc (frontend)
**Target Platform**: Local development (Windows/Linux), Uvicorn backend on port 8000, Vite dev server on port 5173
**Project Type**: Web application (FastAPI REST API + React SPA)
**Performance Goals**: Appraisal workflow under 15 seconds for single image with 3 inference samples (SC-005)
**Constraints**: Multi-sample aggregation multiplies inference time linearly; default 3 samples must stay within 15s budget
**Scale/Scope**: Single-user local tool, ~15 source files affected across backend and frontend

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

| Principle                               | Status | Notes                                                                                                                                                                                    |
| --------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **I. Type Safety & Validation**         | PASS   | New `ColorProportions` Pydantic model replaces fixed 3-color fields. Frontend `AppraisalResult` interface updated. All new config values go through Pydantic.                            |
| **II. Service-Oriented Separation**     | PASS   | New color analyzer stays in `app/services/color_analysis.py`. Multi-sample aggregation added as utility/wrapper, not in router. Price service removed. Config values in `app/config.py`. |
| **III. ML Model Management**            | PASS   | No new model files needed. Existing YOLO models used as-is. Linear regression price models removed. KMeans is runtime-only (no saved model). Lazy loading pattern maintained.            |
| **IV. Testing Discipline**              | PASS   | Existing tests updated to remove price assertions. New tests for color clustering output format and multi-sample aggregation.                                                            |
| **V. Documentation-Driven Development** | PASS   | Feature spec exists. `docs/features/` and `FEATURES_INDEX.md` to be updated. Docstrings required on all new/changed functions.                                                           |
| **VI. Observability & Error Handling**  | PASS   | Logger usage maintained. Edge cases (few pixels, unmapped colors) produce warnings. No bare `print()`.                                                                                   |
| **Tech Stack**                          | PASS   | scikit-learn already in requirements.txt (KMeans). No new dependencies needed.                                                                                                           |

**Gate result**: ALL PASS — proceed to Phase 0.

### Post-Design Re-check (after Phase 1)

| Principle                    | Status | Notes                                                                                                                                                                                                              |
| ---------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **I. Type Safety**           | PASS   | `AppraisalResponse` uses `Dict[str, float]` for `color_proportions` — validated by Pydantic. Frontend uses `Record<string, number>`. All new functions have type hints/JSDoc.                                      |
| **II. Service Separation**   | PASS   | Color analysis stays in `services/`. Multi-sample augmentation is a utility function called from the router (no business logic in router — router orchestrates, helpers compute). Config constants in `config.py`. |
| **III. ML Model Management** | PASS   | No new model files. Removed unused linear models. KMeans runs in-memory, not a persisted model. Lazy loading of YOLO models unchanged.                                                                             |
| **IV. Testing**              | PASS   | Tests updated for new schema. New tests for color proportions format and multi-sample n=1 equivalence.                                                                                                             |
| **V. Documentation**         | PASS   | research.md, data-model.md, contracts/, quickstart.md all generated. Feature docs to be updated in implementation.                                                                                                 |
| **VI. Observability**        | PASS   | Logger used for cluster results, augmentation steps, aggregation outcomes. Edge cases (few pixels → warning, unmapped color → "Other") logged at WARNING level.                                                    |

**Post-design gate result**: ALL PASS — proceed to Phase 2 (tasks).

## Project Structure

### Documentation (this feature)

```text
specs/003-color-sampling-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── config.py              # Remove price model paths, add color/sampling config
│   ├── main.py                # Unchanged
│   ├── train.py               # Remove (price training script)
│   ├── routers/
│   │   └── appraisal.py       # Remove price logic, update response construction, remove /train endpoint
│   ├── schemas/
│   │   └── appraisal.py       # New ColorProportions model, update AppraisalResponse, remove training schemas
│   ├── services/
│   │   ├── color_analysis.py  # Rewrite: K-Means in LAB colorspace
│   │   ├── color_calibration_ui.py  # Remove (no longer needed)
│   │   ├── pattern_detection.py     # Add multi-sample wrapper
│   │   ├── size_detection.py        # Add multi-sample wrapper
│   │   ├── price_prediction.py      # Remove entirely
│   │   └── symmetry_analysis.py     # Unchanged
│   └── utils/
│       └── __init__.py
├── models/
│   ├── koi-segment.pt         # Kept
│   ├── coin.pt                # Kept
│   ├── koi-pattern.pt         # Kept
│   ├── linear_*.json/pkl      # Remove (price models)
│   └── color_calibration.json # Remove (HSV calibration)
└── tests/
    └── test_appraisal.py      # Update for new response schema

frontend/
├── src/
│   ├── App.tsx                # Remove "AI-Powered Fish Valuation" tagline
│   ├── components/
│   │   ├── ResultsPanel.tsx   # Remove price hero card, add criteria-only layout
│   │   ├── ColorDistribution.tsx  # Dynamic named colors instead of fixed 3
│   │   └── MetricCard.tsx     # Unchanged
│   ├── services/
│   │   └── api.ts             # Remove training API call
│   ├── types/
│   │   └── index.ts           # Update AppraisalResult, remove price/training types
│   └── utils/
│       └── exportCsv.ts       # Remove price column, add dynamic color columns
└── package.json               # Unchanged
```

**Structure Decision**: Existing web application structure (backend/ + frontend/) is used. No new directories needed. Changes are modifications/removals within existing files.

## Session Split

| Session                 | Scope                                                                                                         | Key Deliverables                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| **Session 1: Backend**  | Color analysis rewrite, price removal, multi-sample aggregation, schema updates, config updates, test updates | Updated API producing new response format |
| **Session 2: Frontend** | Type updates, ResultsPanel redesign, ColorDistribution dynamic colors, CSV export update, price UI removal    | UI aligned with new API contract          |

## Complexity Tracking

> No constitution violations found — this section is intentionally empty.
