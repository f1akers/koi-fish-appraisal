# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Koi Fish Appraisal -- an AI-powered web app that appraises koi fish from photos using computer vision and machine learning. A user uploads or captures a photo containing a koi fish and a reference coin; the backend runs YOLOv8 segmentation/detection, K-Means color clustering, and symmetry analysis, then returns quality scores.

## Architecture

Monorepo with two top-level applications:

```
backend/          Python 3.10+ / FastAPI  (CV/ML API)
frontend/         React 19 / Vite 7 / Tailwind CSS 4  (SPA)
docs/             Feature specs, formulas, domain docs
.specify/         SpecKit tooling (constitution, templates, scripts)
```

### Backend (FastAPI + Pydantic v2)

- **Entry point**: `backend/app/main.py` -> `app` (FastAPI instance)
- **Routers** (`app/routers/`): HTTP layer only. Single router `appraisal.py` with `POST /api/appraise` and `GET /api/model-status`.
- **Services** (`app/services/`): One service per domain capability -- `size_detection`, `pattern_detection`, `color_analysis`, `color_scoring`, `symmetry_analysis`. Stateless or lazy-loaded singletons for YOLO models.
- **Schemas** (`app/schemas/`): Pydantic v2 DTOs (`AppraisalResponse`, `AppraisalRequest`).
- **Config** (`app/config.py`): All settings via `pydantic-settings`, coin specs, model paths, color analysis constants. No magic numbers in services.
- **Models** (`backend/models/`): YOLOv8 weights -- `koi-segment.pt`, `coin.pt`, `koi-pattern.pt`. Not checked into git.
- **Tests** (`backend/tests/`): pytest + FastAPI TestClient.

### Frontend (React 19 + Vite 7 + Tailwind CSS 4)

- **Entry point**: `frontend/src/main.tsx`
- **Components** (`src/components/`): `CameraCapture`, `FileUpload`, `ResultsPanel`, `ColorDistribution`, `MetricCard`, `GuideOverlay`. Barrel export in `index.ts`.
- **Hooks** (`src/hooks/`): `useCamera` -- camera access and capture.
- **Services** (`src/services/api.ts`): `appraiseImage()` and `checkHealth()` via `fetch`. Uses `VITE_API_BASE_URL` env var or empty string (proxy).
- **Types** (`src/types/index.ts`): TypeScript interfaces matching backend schemas.
- **Utils** (`src/utils/exportCsv.ts`): CSV export for appraisal history.
- **State**: Local React `useState` in `App.tsx` -- no external state management library.
- **API proxy**: Vite dev server proxies `/api` to `http://localhost:8000`.

## Build / Run / Test Commands

### Backend

```bash
# Setup (from repo root)
cd backend
python -m venv venv
# Windows: venv\Scripts\activate  |  Unix: source venv/bin/activate
pip install -r requirements.txt

# Run (development, with reload)
cd backend
uvicorn app.main:app --reload --port 8000

# Run tests
cd backend
pytest

# Lint (if ruff is installed)
cd backend
ruff check .
```

### Frontend

```bash
# Setup
cd frontend
npm install

# Run (development)
cd frontend
npm run dev          # Vite dev server on :5173, proxies /api -> :8000

# Build (production)
cd frontend
npm run build        # runs tsc -b && vite build

# Lint
cd frontend
npm run lint         # ESLint with typescript-eslint

# Preview production build
cd frontend
npm run preview
```

### Convenience Scripts (repo root)

- `setup.bat` / `setup.sh` -- full setup (venv, pip install, npm install, frontend build, model check)
- `run.bat` / `run.sh` -- start both servers concurrently

### Docker

```bash
# Backend
cd backend
docker build -t koi-backend .
docker run -p 8000:8000 koi-backend

# Frontend (pass backend URL at build time)
cd frontend
docker build --build-arg VITE_API_BASE_URL=http://localhost:8000 -t koi-frontend .
docker run -p 80:80 koi-frontend
```

## Tech Stack

| Layer            | Technology                          | Version  |
|------------------|-------------------------------------|----------|
| Backend runtime  | Python                              | 3.10+    |
| Backend framework| FastAPI + Uvicorn                   | 0.109+   |
| Validation       | Pydantic v2 + pydantic-settings     | 2.5+     |
| Computer vision  | OpenCV (opencv-python)              | 4.9+     |
| Object detection | Ultralytics YOLOv8                  | 8.1+     |
| ML clustering    | scikit-learn (KMeans)               | 1.4+     |
| Image processing | Pillow, NumPy, SciPy               |          |
| Frontend         | React (TypeScript, strict mode)     | 19+      |
| Build tool       | Vite                                | 7+       |
| CSS              | Tailwind CSS                        | 4+       |
| Linting (FE)     | ESLint + typescript-eslint          | 9+       |
| Testing (BE)     | pytest + httpx + FastAPI TestClient  | 7.4+    |

## API Endpoints

All endpoints are prefixed with `/api`:

| Method | Path            | Purpose                              |
|--------|-----------------|--------------------------------------|
| POST   | /api/appraise   | Upload image, get full appraisal     |
| GET    | /api/model-status | Check ML model availability        |
| GET    | /api/health     | Health check                         |

The appraisal endpoint accepts `multipart/form-data` with an `image` file field and returns `AppraisalResponse` JSON.

## Environment Variables

### Backend (`backend/.env`)

| Variable          | Default                                    | Purpose                |
|-------------------|--------------------------------------------|------------------------|
| `DEBUG`           | `True`                                     | Enable debug/reload    |
| `MODEL_PATH`      | `./models`                                 | Path to YOLO weights   |
| `IMAGES_PATH`     | `./images`                                 | Path to image assets   |
| `ALLOWED_ORIGINS` | `http://localhost:5173,...`                 | CORS origins (CSV)     |

### Frontend (build-time)

| Variable             | Purpose                                    |
|----------------------|--------------------------------------------|
| `VITE_API_BASE_URL`  | Backend URL for production (empty = proxy) |

## Code Style & Conventions

### Python (Backend)

- Type hints on all function parameters and return values.
- All API request/response models use Pydantic `BaseModel` with `Field` constraints.
- Module-level docstrings required. Public functions need `Args`/`Returns`/`Raises` docstrings.
- Use `logging.getLogger(__name__)` -- never bare `print()`.
- All config values (thresholds, paths, magic numbers) live in `app/config.py`.
- Services are stateless or use lazy-loaded singletons for model instances.

### TypeScript (Frontend)

- Strict TypeScript (`strict: true`, `noUnusedLocals`, `noUnusedParameters`).
- No `any` -- use `unknown` + type guards. Prefer union types and enums.
- Every API contract has a corresponding TypeScript interface in `src/types/`.
- JSDoc file-level comments on all modules; JSDoc on public exports.
- Boolean state variables prefixed with `is`/`has`/`can`/`should`.

### General

- SRP: one function = one job. Aim for 20-40 lines max per function.
- Extract repeated logic into shared utilities immediately.
- Never leave dead code or commented-out blocks.
- Handle or rethrow errors with context; never silently swallow.
- Validate inputs at the boundary (router/controller); trust data internally.
- Prefer `async/await` over `.then()` chains.
- Imports sorted: external libraries, then internal modules, then local files.
- Constants in `SCREAMING_SNAKE_CASE`. Types/interfaces in `PascalCase`. Functions/variables in `camelCase`.
- Commit messages: `type: short description` (feat, fix, docs, refactor, test, chore).

## ML Pipeline

The appraisal pipeline processes an uploaded image through these stages:

1. **Size detection** -- YOLOv8 segmentation (`koi-segment.pt`) finds the fish mask; YOLOv8 detection (`coin.pt`) finds the reference coin. Pixel-to-cm ratio calculated from coin diameter. Multi-sample aggregation (median of N runs).
2. **Pattern classification** -- YOLOv8 classification (`koi-pattern.pt`) with majority vote over N augmented samples. Patterns: `ogon`, `sanke`, `kohaku`.
3. **Color analysis** -- K-Means clustering (k=4) in CIELAB colorspace on masked fish pixels. Centroids mapped to named koi colors (White, Red, Black, Orange, Yellow) via Euclidean distance.
4. **Symmetry analysis** -- PCA-aligned fish mask split into 5 longitudinal sections; bilateral comparison yields symmetry score 0-1.
5. **Color scoring** -- Actual color proportions scored against pattern-specific ideal distributions.
6. **Overall score** -- Mean of color score and symmetry score.

## Key Domain Concepts

- **Reference coin**: Philippine Peso coins used for size calibration (diameter mappings in `app/config.py`).
- **Koi patterns**: Ogon (single color), Sanke (red/white/black), Kohaku (red/white).
- **Color map**: Static LAB centroids for 5 named koi colors in OpenCV uint8 encoding.
- **Multi-sample aggregation**: N inference runs with augmentation to reduce variance.
