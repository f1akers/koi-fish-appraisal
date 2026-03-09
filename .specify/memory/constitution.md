<!--
  Sync Impact Report
  ====================================================================
  Version change: 0.0.0 → 1.0.0 (MAJOR — initial constitution adoption)
  Modified principles: N/A (initial version)
  Added sections:
    - Core Principles (6 principles)
    - Technology Stack Constraints
    - Development Workflow & Quality Gates
    - Governance
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md         ✅ compatible
    - .specify/templates/spec-template.md          ✅ compatible
    - .specify/templates/tasks-template.md         ✅ compatible
    - .specify/templates/checklist-template.md     ✅ compatible
  Follow-up TODOs: None
  ====================================================================
-->

# Koi Fish Appraisal Constitution

## Core Principles

### I. Type Safety & Validation

All data crossing boundaries MUST be validated through typed schemas.

- **Backend**: Every API request and response MUST use Pydantic `BaseModel`
  subclasses with `Field` constraints (e.g., `ge`, `le`, descriptions).
  All functions MUST include Python type hints for parameters and return
  values.
- **Frontend**: Strict TypeScript (`tsconfig` strict mode) is
  non-negotiable. Every API contract MUST have a corresponding
  TypeScript `interface` in `frontend/src/types/`. Union types and
  enums MUST be preferred over `any` or `unknown`.
- **Rationale**: The ML pipeline produces numeric metrics that flow from
  OpenCV → service → router → JSON → React component. A single
  unvalidated value corrupts the entire appraisal result.

### II. Service-Oriented Separation

Backend code MUST follow a layered architecture with clear
responsibilities.

- **Routers** (`app/routers/`): HTTP concerns only — receive requests,
  call services, return responses. No business logic.
- **Services** (`app/services/`): One service per domain capability
  (size detection, pattern detection, color analysis, symmetry
  analysis, price prediction). Services MUST be stateless or use
  lazy-loaded singletons for model instances.
- **Schemas** (`app/schemas/`): Data transfer objects only. No methods
  beyond Pydantic validators.
- **Config** (`app/config.py`): All magic numbers, file paths, and
  environment-dependent values MUST live here. Hard-coded paths or
  thresholds in service files are prohibited.
- **Rationale**: Each CV/ML service can be developed, tested, and
  swapped independently. Router changes never break model inference.

### III. ML Model Management

Machine learning models MUST be treated as versioned, lazy-loaded
artifacts.

- Models MUST reside in `backend/models/` with clear naming
  (`koi-segment.pt`, `coin.pt`, `koi-pattern.pt`,
  `linear_<pattern>.json`).
- Model loading MUST use lazy initialization (Python `@property` or
  equivalent) to avoid startup-time penalties and allow graceful
  degradation when a model file is missing.
- Training scripts MUST accept CSV + image directory inputs and produce
  reproducible model artifacts. Training configuration MUST be
  exposed via Pydantic schemas.
- Model file paths MUST be resolved through `app/config.MODEL_PATHS`,
  never constructed inline.
- **Rationale**: YOLOv8 and scikit-learn models are large and
  pattern-specific. Lazy loading keeps cold-start fast; centralized
  paths prevent "file not found" drift across services.

### IV. Testing Discipline

Every API endpoint MUST have at least smoke-level test coverage.

- Tests MUST use `pytest` with FastAPI `TestClient`.
- Endpoint tests MUST cover: valid request → 200, missing input → 422,
  invalid input → 400, and missing model → 503.
- Service-level unit tests SHOULD mock model inference to run without
  GPU/model files.
- Frontend SHOULD include component-level tests for critical flows
  (capture, results display).
- Tests MUST be runnable via `pytest` from the `backend/` directory
  and `npm run lint` (+ future `npm test`) from `frontend/`.
- **Rationale**: CV pipelines are brittle to image format and shape
  changes. Automated tests catch regressions before deployment.

### V. Documentation-Driven Development

Features MUST be documented before, during, and after implementation.

- Every feature MUST have a corresponding spec in `docs/features/`.
- Feature status MUST be tracked in `docs/FEATURES_INDEX.md` using
  the 🔴/🟡/🟢 status convention.
- All Python modules MUST have a module-level docstring explaining
  purpose. All public classes and functions MUST have docstrings
  with `Args`/`Returns`/`Raises` sections.
- All TypeScript modules MUST have JSDoc file-level comments. Public
  interfaces and exported functions MUST have JSDoc descriptions.
- **Rationale**: The project combines multiple ML models and CV
  techniques. Without inline and feature-level docs, onboarding
  cost grows exponentially.

### VI. Observability & Error Handling

All services MUST produce structured logs and surface actionable
errors.

- Python services MUST use `logging.getLogger(__name__)` — never
  bare `print()`.
- Log levels: `INFO` for model loads and request lifecycle, `WARNING`
  for recoverable issues (no mask found, calibration fallback),
  `ERROR` for unrecoverable failures.
- FastAPI routers MUST map domain exceptions to appropriate HTTP
  status codes: `422` for detection failures, `503` for missing
  models, `400` for invalid input.
- Frontend MUST display user-friendly error messages and MUST NOT
  expose raw stack traces or internal paths.
- **Rationale**: ML inference fails silently in subtle ways (wrong
  mask shape, empty detections). Structured logging is the primary
  debugging tool in production.

## Technology Stack Constraints

The following technology choices are fixed and MUST NOT be changed
without a constitution amendment.

| Layer              | Required Technology             | Minimum Version |
| ------------------ | ------------------------------- | --------------- |
| Backend runtime    | Python                          | 3.10+           |
| Backend framework  | FastAPI + Uvicorn               | 0.109+          |
| Data validation    | Pydantic v2 + pydantic-settings | 2.5+            |
| Computer vision    | OpenCV (opencv-python)          | 4.9+            |
| Object detection   | Ultralytics YOLOv8              | 8.1+            |
| Regression         | scikit-learn                    | 1.4+            |
| Frontend runtime   | Node.js                         | 18+             |
| Frontend framework | React (TypeScript)              | 19+             |
| Build tool         | Vite                            | 7+              |
| CSS framework      | Tailwind CSS                    | 4+              |
| Linting (frontend) | ESLint + typescript-eslint      | 9+              |

- New backend dependencies MUST be added to
  `backend/requirements.txt` with minimum version pins.
- New frontend dependencies MUST be added to `frontend/package.json`.
- Binary/native dependencies MUST be documented in the project
  `README.md` setup section.

## Development Workflow & Quality Gates

### Local Development

1. Backend: `uvicorn app.main:app --reload --port 8000` from
   `backend/` with virtual environment activated.
2. Frontend: `npm run dev` from `frontend/` (Vite dev server on
   port 5173 with API proxy).
3. Both servers MUST run concurrently during development. The
   `run.bat` / `run.sh` scripts automate this.

### Quality Gates (pre-commit / pre-merge)

| Gate            | Command                        | Pass Criteria           |
| --------------- | ------------------------------ | ----------------------- |
| Backend tests   | `cd backend && pytest`         | All tests pass          |
| Frontend lint   | `cd frontend && npm run lint`  | Zero errors             |
| Frontend build  | `cd frontend && npm run build` | `tsc -b` + Vite succeed |
| Type check (FE) | Included in build              | No TypeScript errors    |

- Code MUST NOT be merged if any quality gate fails.
- New features MUST include at minimum one test per new endpoint and
  updated documentation in `docs/`.

### Branch & Commit Conventions

- Feature work SHOULD use descriptive branch names
  (e.g., `feature/color-calibration`, `fix/coin-detection`).
- Commit messages MUST follow conventional format:
  `type: short description` where type is one of `feat`, `fix`,
  `docs`, `refactor`, `test`, `chore`.

## Governance

This constitution is the authoritative source for project standards.
All code reviews, pull requests, and automated checks MUST verify
compliance with the principles defined above.

- **Amendments**: Any change to this constitution MUST be documented
  with a version bump, rationale, and updated `Last Amended` date.
  Principle additions or removals require MAJOR version increments.
  Clarifications require PATCH increments.
- **Compliance review**: At the start of each new feature, the
  implementation plan MUST include a "Constitution Check" section
  confirming alignment with all active principles.
- **Conflict resolution**: If a principle conflicts with a practical
  implementation need, the deviation MUST be documented in the
  plan's "Complexity Tracking" table with justification and the
  simpler alternative that was rejected.
- **Guidance**: Use `docs/FEATURES_INDEX.md` and feature-specific
  docs in `docs/features/` for runtime development guidance.

**Version**: 1.0.0 | **Ratified**: 2026-03-09 | **Last Amended**: 2026-03-09
