# Koi Fish Appraisal - Features Index

> **Project Overview:** A web application for appraising Koi fish through multiple factors using machine learning and computer vision.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python, FastAPI, OpenCV, Ultralytics |
| **Frontend** | Vite, React (TypeScript), Tailwind CSS |
| **ML Models** | YOLOv8 (Segmentation/Detection), Scikit-learn (Linear Regression) |

---

## Features Overview

| Feature | Status | Documentation |
|---------|--------|---------------|
| Feature 1: Fish Metrics | 🟢 Completed | [fish-metrics.md](./features/fish-metrics.md) |
| Feature 2: Linear Regression Trainer | 🟢 Completed | [linear-regression-trainer.md](./features/linear-regression-trainer.md) |
| Feature 3: Frontend Camera Capture | 🟢 Completed | [frontend-capture.md](./features/frontend-capture.md) |
| Feature 4: Results Display & Export | 🟢 Completed | [results-display.md](./features/results-display.md) |

### Status Legend
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Completed

---

## Feature 1: Fish Metrics

**Description:** Calculate numerical metrics from koi fish images for price prediction.

### Sub-features:
1. **Size Detection** - Detect fish segmentation, use reference coin for scale
2. **Pattern Recognition** - Classify patterns (Ogon, Showa, Kohaku)
3. **Color Analysis** - Quantify color distribution using levels-based approach
4. **Symmetry Analysis** - PCA + Chi-squared comparison of left/right sides
5. **Price Prediction** - Process metrics through trained linear regression model

### Required Models:
- `backend/models/koi-segment.pt` - Instance segmentation model
- `backend/models/coin.pt` - Coin detection model
- `backend/models/koi-pattern.pt` - Pattern classification model
- `backend/models/linear.pkl` - Trained linear regression model

---

## Feature 2: Linear Regression Trainer

**Description:** Training script for the price prediction model.

### Input:
- CSV file with columns: `image_filename`, `price`
- Images stored at `backend/images/`

### Output:
- Trained model saved to `backend/models/linear.pkl`

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
- Show individual metrics (size, pattern, color, symmetry)
- Display price prediction
- Linear regression visualization graph
- Export results to CSV

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

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/appraise` | Upload image and get appraisal |
| POST | `/api/train` | Trigger model training |
| GET | `/api/health` | Health check endpoint |

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
