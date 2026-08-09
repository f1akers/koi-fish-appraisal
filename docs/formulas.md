# Koi Assessment Formulas

## Color Scoring

Compares the fish's actual color distribution against a pattern-specific ideal.

### Ideal Distributions

| Pattern | Red | White | Black |
|---------|-----|-------|-------|
| Sanke   | 50% | 30%   | 20%   |
| Kohaku  | 60% | 40%   | —     |
| Ogon    | —   | —     | —     |

### Formula

For Sanke and Kohaku, the score is derived from total absolute deviation:

```
total_deviation = Σ |actual(color) - ideal(color)|   for each color in ideal
                + Σ actual(color)                     for each color NOT in ideal

color_score = max(0, 1 - total_deviation / 200)
```

`200` is the maximum possible total deviation (no overlap between actual and ideal).

For Ogon (uniform single color):

```
color_score = max(actual color proportions) / 100
```

**Range:** 0–1 (1 = perfect match to ideal)

---

## Symmetry Scoring

Based on: *Evaluation of Body Color Pattern in Koi (Cyprinus rubrofuscus) Using Image Analysis*, Fishes (MDPI), Vol. 7, No. 4, Article 158. DOI: 10.3390/fishes7040158

### Method

1. **Align** — PCA rotates the fish to vertical (head up).
2. **Crop** — Bounding box crop to fish content.
3. **Section** — Fish height divided into 5 equal longitudinal sections.
4. **Score each section** — For each section `i`, count pattern pixels left and right of the vertical midline:

```
S_i = min(A_left_i, A_right_i) / max(A_left_i, A_right_i)
```

Sections with zero pixels on both sides score `1.0` (trivially symmetric).

5. **Aggregate** — Mean across all 5 sections:

```
S_overall = (1/5) × Σ S_i   for i = 1..5
```

**Range:** 0–1 (1 = perfect bilateral symmetry across all sections)

---

## Learned Scoring (XGBoost, Expert-Calibrated)

When `SCORING_MODE=learned` and trained models exist, the quality scores
(color, pattern, symmetry, overall) come from XGBoost regressors instead
of the heuristic formulas above. The models predict what a panel of
experts would rate the fish (1–5 scale), trained on expert-labeled images.

### Architecture

- **Per pattern type** (sanke / kohaku / ogon): 4 models each = 12 total.
- **Targets**: expert `color`, `pattern`, `symmetry`, `overall` ratings (1–5, 1 decimal).
- **Features** (same for training and serving, see `FEATURE_COLUMNS` in
  `app/utils/feature_extraction.py`):
  - One-hot `pattern_ogon/sanke/kohaku`, `pattern_confidence`
  - `symmetry_score`, heuristic `color_score` (prior)
  - Color proportions for White, Red, Black, Orange, Yellow
  - Fish size is intentionally **not** a feature (training images have no coin);
    the size measurement is still computed and displayed by the app.
- **Overall** is a 4th-stage model trained on raw features + the 3 predicted scores.

### Training

```
cd backend
python -m app.train \
    --csvs "sanke:training/sanke.csv,kohaku:training/kohaku.csv,ogon:training/ogon.csv" \
    --images-root ./training
```

- Expert CSVs: one per type, columns `filename,color,pattern,symmetry,overall`;
  one row per expert rating (same filename up to 4×).
- CV: GroupKFold grouped by filename — the 4 ratings of one image never span folds.
- Outputs in `training/results/`: `metrics.csv` (MAE/RMSE/R² vs heuristic baseline),
  `predictions_oof.csv`, and thesis-ready confusion matrices
  (`confusion_<target>_<xgb|heuristic>.csv` + `_pct` row-normalized versions).
- Production models saved to `backend/models/expert/<type>_<target>.json`
  (gitignored, generated).

### Serving

- `app/services/expert_scoring.py` lazy-loads the 12 models keyed by detected pattern.
- Router uses them when `SCORING_MODE=learned` (default `heuristic`); falls back
  to heuristics if models are missing.
- Response gains `pattern_score` and `scoring_mode` fields; scores are 0–1
  (predicted 1–5 rating normalized).

---

## Overall Score (Heuristic)

Weighted combination (matches `app/routers/appraisal.py`):

```
overall_score = 0.50 * symmetry_score
              + 0.30 * color_score
              + 0.20 * pattern_confidence
```

**Range:** 0–1
