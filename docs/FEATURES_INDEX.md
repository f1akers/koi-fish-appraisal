# Koi Fish Appraisal - Features Index

> **Project Overview:** A web application for appraising Koi fish through multiple factors using machine learning and computer vision.

## Tech Stack

| Layer         | Technology                                                         |
| ------------- | ------------------------------------------------------------------ |
| **Backend**   | Python, FastAPI, OpenCV, Ultralytics                               |
| **Frontend**  | Vite, React (TypeScript), Tailwind CSS                             |
| **ML Models** | YOLOv8 (Segmentation/Detection), Scikit-learn (K-Means Clustering) |

---

## Features Overview

| Feature                                  | Status       | Documentation                                                               |
| ---------------------------------------- | ------------ | --------------------------------------------------------------------------- |
| Feature 1: Fish Metrics                  | 🟢 Completed | [fish-metrics.md](./features/fish-metrics.md)                               |
| Feature 2: ~~Linear Regression Trainer~~ | 🔴 Removed   | ~~[linear-regression-trainer.md](./features/linear-regression-trainer.md)~~ |
| Feature 3: Frontend Camera Capture       | 🟢 Completed | [frontend-capture.md](./features/frontend-capture.md)                       |
| Feature 4: Results Display & Export      | 🟢 Completed | [results-display.md](./features/results-display.md)                         |
| Feature 5: Expert Scoring (XGBoost)      | 🟡 In Progress | [formulas.md](../formulas.md#learned-scoring-xgboost-expert-calibrated)   |
| Refactor: Color & Sampling               | 🟢 Completed | [spec](../specs/003-color-sampling-refactor/spec.md)                        |

### Status Legend

- 🔴 Not Started
- 🟡 In Progress
- 🟢 Completed

---

## Feature 1: Fish Metrics

**Description:** Calculate numerical metrics from koi fish images for price prediction.

### Sub-features:

1. **Size Detection** - Detect fish segmentation, use reference coin for scale (multi-sample median aggregation)
2. **Pattern Recognition** - Classify patterns (Ogon, Sanke, Kohaku) with multi-sample majority vote
3. **Color Analysis** - K-Means clustering in CIELAB colorspace with named koi color mapping
4. **Symmetry Analysis** - PCA + Chi-squared comparison of left/right sides

### Required Models:

- `backend/models/koi-segment.pt` - Instance segmentation model
- `backend/models/coin.pt` - Coin detection model
- `backend/models/koi-pattern.pt` - Pattern classification model

---

## Feature 2: Linear Regression Trainer (REMOVED)

**Status:** Removed as part of color & sampling refactor (spec 003). Price prediction functionality has been removed.

---

## Feature 3: Frontend Camera Capture

**Description:** Camera interface for capturing koi fish images.

### Requirements:

- Access user's camera
- Display live preview
- Capture button functionality
- Send captured image to backend API

---

## Feature 4: Results Display & Export

**Description:** Display appraisal results and allow data export.

### Requirements:

- Show individual metrics (size, pattern, color distribution, symmetry)
- Dynamic named color bars (Red, White, Black, Orange, Yellow)
- Export results to CSV with dynamic color columns

---

## Development Guidelines

### Code Practices

1. **Backend (Python)**
   - Follow PEP 8 style guide
   - Use type hints for all functions
   - Write docstrings for modules, classes, and functions
   - Create unit tests for each feature
   - Use async/await for I/O operations in FastAPI

2. **Frontend (TypeScript)**
   - Use strict TypeScript configuration
   - Follow React best practices (functional components, hooks)
   - Implement proper error boundaries
   - Use proper state management
   - Write component tests

3. **General**
   - Write meaningful commit messages
   - Create feature branches for development
   - Update documentation when feature is completed
   - Review and update this index when feature status changes

### Documentation Updates

When completing a feature:

1. Update the feature status in this index (🔴 → 🟡 → 🟢)
2. Update the corresponding feature documentation in `docs/features/`
3. Add any API documentation to `docs/api/` if applicable
4. Document any environment variables or configuration changes

---

## API Endpoints (Planned)

| Method | Endpoint        | Description                    |
| ------ | --------------- | ------------------------------ |
| POST   | `/api/appraise` | Upload image and get appraisal |
| GET    | `/api/health`   | Health check endpoint          |

---

## Project Structure

```
koi/
├── docs/
│   ├── FEATURES_INDEX.md
│   ├── koi spec.md
│   ├── coin_sizes.md
│   └── features/
│       ├── fish-metrics.md
│       ├── linear-regression-trainer.md
│       ├── frontend-capture.md
│       └── results-display.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   ├── services/
│   │   ├── models/
│   │   └── utils/
│   ├── models/          # ML model files (.pt, .pkl)
│   ├── images/          # Training images
│   ├── requirements.txt
│   └── README.md
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── hooks/
    │   ├── services/
    │   ├── types/
    │   └── App.tsx
    ├── package.json
    └── README.md
```
