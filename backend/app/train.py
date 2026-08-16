"""
Expert Scoring Trainer

Trains XGBoost regressors that predict expert quality ratings
(color, pattern, symmetry, overall on a 1-5 scale) from the vision
pipeline features (symmetry, color proportions, pattern confidence).

Pipeline:
1. Parse one expert ratings CSV per pattern type (all experts merged,
   one row per rating; the same filename may appear up to 4 times).
2. Extract pipeline features per unique image (coin-free).
3. Save an intermediate dataset CSV per type (features + ratings).
4. Train with GroupKFold cross-validation grouped by filename so the
   4 ratings of one image never span train/test folds.
5. Emit evaluation metrics and thesis-ready confusion matrices (OOF).
6. Refit production models on the full dataset and save them as
   XGBoost JSON files for app/services/expert_scoring.py.

Usage:
    python -m app.train \
        --csvs "sanke:training/sanke.csv,kohaku:training/kohaku.csv,ogon:training/ogon.csv" \
        --images-root ./training
"""

import argparse
import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from xgboost import XGBRegressor

from app.config import (
    EXPERT_MODEL_DIR,
    EXPERT_SCORE_CSV_COLUMNS,
    EXPERT_SCORE_MAX,
    EXPERT_SCORE_MIN,
    EXPERT_TARGETS,
    KOI_PATTERNS,
)
from app.utils.feature_extraction import FEATURE_COLUMNS, extract_appraisal_features

logger = logging.getLogger(__name__)

STAGE1_TARGETS = ["color", "pattern", "symmetry"]
OVERALL_TARGET = "overall"

XGB_PARAMS: dict = {
    "n_estimators": 600,
    "learning_rate": 0.05,
    "max_depth": 3,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "reg:squarederror",
    "tree_method": "hist",
}

RATING_FRACTION_RE = re.compile(r"^(\d+(?:\.\d)?)\s*/\s*5$")


# =============================================================================
# CSV parsing
# =============================================================================


def _coerce_rating(value: object) -> float | None:
    """
    Coerce a raw rating cell to float, or None if not numeric.

    Accepts plain numbers and 'x/5' fraction notation (e.g. '4/5' -> 4.0),
    which some raters use to mean 'x out of 5'.

    Args:
        value: Raw cell value from the CSV.

    Returns:
        Rating as float, or None if it cannot be parsed.
    """
    if isinstance(value, str):
        match = RATING_FRACTION_RE.match(value.strip())
        if match:
            return float(match.group(1))
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_expert_csv(csv_path: Path, pattern_type: str) -> pd.DataFrame:
    """
    Parse and validate one per-type expert ratings CSV.

    Expected columns: filename, color, pattern, symmetry, overall.
    Ratings are 1-5 with at most one decimal place. Rows are individual
    expert ratings; filenames may repeat.

    Rows with unparseable, out-of-range, or over-precise ratings are
    dropped individually (with a warning) so a few stray cells do not
    block the whole dataset. 'x/5' fraction notation is coerced to x.

    Args:
        csv_path: Path to the CSV file.
        pattern_type: One of the KOI_PATTERNS types.

    Returns:
        DataFrame with validated ratings and a 'type' column.
    """
    df = pd.read_csv(csv_path)

    # Normalize headers: strip whitespace/case, unify 'file name' variants
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={"file_name": "filename"})

    missing = [c for c in EXPERT_SCORE_CSV_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{csv_path}: missing columns {missing}")

    dropped: list[dict[str, object]] = []
    cleaned_rows: list[pd.Series] = []
    for _, row in df.iterrows():
        filename = str(row["filename"]).strip() if pd.notna(row["filename"]) else ""
        if not filename:
            dropped.append({"filename": "<blank>", "reason": "blank filename"})
            continue

        values = {col: _coerce_rating(row[col]) for col in EXPERT_TARGETS}
        if any(v is None for v in values.values()):
            dropped.append(
                {
                    "filename": filename,
                    "reason": "non-numeric",
                    "values": values,
                }
            )
            continue
        if any(v < EXPERT_SCORE_MIN or v > EXPERT_SCORE_MAX for v in values.values()):
            dropped.append(
                {
                    "filename": filename,
                    "reason": f"outside {EXPERT_SCORE_MIN}-{EXPERT_SCORE_MAX}",
                    "values": values,
                }
            )
            continue
        decimals = [abs(v * 10 - round(v * 10)) for v in values.values()]
        if any(d > 1e-6 for d in decimals):
            dropped.append(
                {
                    "filename": filename,
                    "reason": "more than 1 decimal place",
                    "values": values,
                }
            )
            continue

        for col in EXPERT_TARGETS:
            row[col] = values[col]
        cleaned_rows.append(row)

    for d in dropped:
        logger.warning(f"Dropped rating row {d['filename']}: {d['reason']} {d.get('values', '')}")

    df = pd.DataFrame(cleaned_rows, columns=df.columns)
    df["type"] = pattern_type
    df["filename"] = df["filename"].astype(str).str.strip()
    if dropped:
        logger.warning(
            f"{csv_path}: dropped {len(dropped)} of {len(df) + len(dropped)} rating rows"
        )
    logger.info(
        f"Parsed {csv_path}: {len(df)} ratings, {df['filename'].nunique()} unique images"
    )
    return df


# =============================================================================
# Dataset building (feature extraction pass)
# =============================================================================


def build_type_dataset(
    ratings: pd.DataFrame,
    images_root: Path,
    dataset_path: Path,
) -> pd.DataFrame:
    """
    Extract pipeline features for every unique image in the ratings and
    merge them onto each rating row. Saves the intermediate CSV.

    Args:
        ratings: Parsed expert ratings for one pattern type.
        images_root: Root directory with a subfolder per pattern type.
        dataset_path: Where to save the intermediate dataset CSV.

    Returns:
        Dataset DataFrame with features + ratings, or empty if no images
        could be processed.
    """
    pattern_type = ratings["type"].iloc[0]
    image_dir = images_root / pattern_type

    features_by_filename: dict[str, dict[str, float] | None] = {}
    for filename in ratings["filename"].unique():
        image_path = image_dir / filename
        if not image_path.exists():
            logger.warning(f"Image not found: {image_path}")
            features_by_filename[filename] = None
            continue
        features_by_filename[filename] = extract_appraisal_features(str(image_path))

    failed = [f for f, feat in features_by_filename.items() if feat is None]
    if failed:
        logger.warning(f"Dropping {len(failed)} images with failed extraction: {failed[:10]}")

    feature_rows = [
        (filename, feat)
        for filename, feat in features_by_filename.items()
        if feat is not None
    ]
    if not feature_rows:
        logger.error(f"No images could be processed for {pattern_type}")
        return pd.DataFrame()

    feature_df = pd.DataFrame(
        [feat for _, feat in feature_rows],
        index=[f for f, _ in feature_rows],
    )
    feature_df.index.name = "filename"

    dataset = ratings.merge(feature_df, left_on="filename", right_index=True, how="inner")
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(dataset_path, index=False)
    logger.info(f"Saved dataset ({len(dataset)} rows) to {dataset_path}")
    return dataset


def load_datasets(
    csvs: dict[str, Path],
    images_root: Path,
    dataset_dir: Path,
    skip_features: bool,
) -> dict[str, pd.DataFrame]:
    """
    Build or load the intermediate dataset per pattern type.

    Args:
        csvs: Mapping of pattern type to expert ratings CSV path.
        images_root: Directory with one image subfolder per type.
        dataset_dir: Where intermediate dataset CSVs live.
        skip_features: If True, load existing dataset CSVs without re-extraction.

    Returns:
        Mapping of pattern type to dataset DataFrame.
    """
    datasets: dict[str, pd.DataFrame] = {}
    for pattern_type, csv_path in csvs.items():
        dataset_path = dataset_dir / f"dataset_{pattern_type}.csv"
        if skip_features and dataset_path.exists():
            dataset = pd.read_csv(dataset_path)
            logger.info(f"Loaded existing dataset ({len(dataset)} rows): {dataset_path}")
        else:
            ratings = parse_expert_csv(csv_path, pattern_type)
            dataset = build_type_dataset(ratings, images_root, dataset_path)
        datasets[pattern_type] = dataset
    return datasets


# =============================================================================
# Training with GroupKFold (out-of-fold predictions)
# =============================================================================


def _oof_predictions(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    folds: int,
    seed: int,
    extra_features: np.ndarray | None = None,
) -> np.ndarray:
    """
    Train a model with GroupKFold and return out-of-fold predictions.

    Args:
        X: Base feature matrix.
        y: Target values.
        groups: Group labels (filename) — never split a group across folds.
        folds: Number of CV folds.
        seed: Random seed.
        extra_features: Optional additional features (e.g. stage-1 OOF
            predictions for the overall model).

    Returns:
        Out-of-fold predictions aligned with y.
    """
    X_full = X if extra_features is None else np.hstack([X, extra_features])
    oof = np.full(len(y), np.nan)
    splitter = GroupKFold(n_splits=folds)

    for train_idx, val_idx in splitter.split(X_full, y, groups=groups):
        model = XGBRegressor(**XGB_PARAMS, random_state=seed)
        model.fit(X_full[train_idx], y[train_idx])
        oof[val_idx] = model.predict(X_full[val_idx])

    return oof


def _heuristic_predictions(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """
    Convert current heuristic 0-1 scores to the 1-5 expert scale.

    The overall heuristic mirrors app/routers/appraisal.py:
    0.5 * symmetry + 0.3 * color + 0.2 * pattern_confidence.
    """
    symmetry = df["symmetry_score"].to_numpy(dtype=float)
    color = df["color_score"].to_numpy(dtype=float)
    confidence = df["pattern_confidence"].to_numpy(dtype=float)

    return {
        "color": color * EXPERT_SCORE_MAX,
        "pattern": confidence * EXPERT_SCORE_MAX,
        "symmetry": symmetry * EXPERT_SCORE_MAX,
        "overall": (0.5 * symmetry + 0.3 * color + 0.2 * confidence) * EXPERT_SCORE_MAX,
    }


def train_type(
    df: pd.DataFrame,
    folds: int,
    seed: int,
) -> pd.DataFrame:
    """
    Run GroupKFold CV for all targets on one pattern type.

    Stage 1: color, pattern, symmetry (raw features).
    Stage 2: overall (raw features + stage-1 OOF predictions).

    Args:
        df: Dataset DataFrame for one type.
        folds: Number of CV folds.
        seed: Random seed.

    Returns:
        OOF prediction DataFrame (one row per rating) including the
        heuristic baseline predictions.
    """
    X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    groups = df["filename"].to_numpy()
    heuristic = _heuristic_predictions(df)

    oof: dict[str, np.ndarray] = {}
    stage1_oof: list[np.ndarray] = []

    for target in STAGE1_TARGETS:
        y = df[target].to_numpy(dtype=float)
        oof[target] = _oof_predictions(X, y, groups, folds, seed)
        stage1_oof.append(oof[target])

    y_overall = df[OVERALL_TARGET].to_numpy(dtype=float)
    oof[OVERALL_TARGET] = _oof_predictions(
        X, y_overall, groups, folds, seed, extra_features=np.column_stack(stage1_oof)
    )

    result = df[["filename", "type"]].copy()
    for target in EXPERT_TARGETS:
        result[f"actual_{target}"] = df[target].to_numpy(dtype=float)
        result[f"pred_xgb_{target}"] = oof[target]
        result[f"pred_heuristic_{target}"] = heuristic[target]
    return result


# =============================================================================
# Evaluation + confusion matrices
# =============================================================================


def evaluate(oof_by_type: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Compute MAE, RMSE, and R2 for XGBoost and heuristic baselines.

    Args:
        oof_by_type: OOF prediction DataFrames per pattern type.

    Returns:
        Metrics DataFrame with one row per (type, target, model).
    """
    rows: list[dict] = []
    for pattern_type, oof in oof_by_type.items():
        rows.extend(_metric_rows(oof, pattern_type))

    pooled = pd.concat(oof_by_type.values(), ignore_index=True)
    rows.extend(_metric_rows(pooled, "pooled"))
    return pd.DataFrame(rows)


def _metric_rows(oof: pd.DataFrame, label: str) -> list[dict]:
    """Metric rows for one label (a type or 'pooled')."""
    rows: list[dict] = []
    for target in EXPERT_TARGETS:
        actual = oof[f"actual_{target}"].to_numpy(dtype=float)
        for model in ("xgb", "heuristic"):
            pred = oof[f"pred_{model}_{target}"].to_numpy(dtype=float)
            rows.append(
                {
                    "type": label,
                    "target": target,
                    "model": model,
                    "mae": float(mean_absolute_error(actual, pred)),
                    "rmse": float(np.sqrt(mean_squared_error(actual, pred))),
                    "r2": float(r2_score(actual, pred)),
                }
            )
    return rows


def write_confusion_matrices(
    pooled_oof: pd.DataFrame,
    results_dir: Path,
) -> None:
    """
    Write confusion matrices (expert vs predicted, integer 1-5 bins).

    One CSV per (target, model): counts plus a row-normalized percent
    version. Predictions are the honest out-of-fold values.

    Args:
        pooled_oof: OOF predictions pooled across all types.
        results_dir: Directory to write CSVs into.
    """
    labels = list(range(1, 6))

    for target in EXPERT_TARGETS:
        actual = np.rint(pooled_oof[f"actual_{target}"]).clip(1, 5).astype(int)
        for model in ("xgb", "heuristic"):
            pred = np.rint(pooled_oof[f"pred_{model}_{target}"]).clip(1, 5).astype(int)
            counts = pd.crosstab(
                pd.Series(actual, name="expert"),
                pd.Series(pred, name="predicted"),
                rownames=["expert"],
                colnames=["predicted"],
            )
            counts = counts.reindex(index=labels, columns=labels, fill_value=0)

            counts.to_csv(results_dir / f"confusion_{target}_{model}.csv")
            row_sums = counts.sum(axis=1).replace(0, np.nan)
            pct = counts.div(row_sums, axis=0).fillna(0.0).round(4)
            pct.to_csv(results_dir / f"confusion_{target}_{model}_pct.csv")

    logger.info(f"Confusion matrices written to {results_dir}")


# =============================================================================
# Production model refit + save
# =============================================================================


def refit_production_models(
    datasets: dict[str, pd.DataFrame],
    models_dir: Path,
    seed: int,
) -> None:
    """
    Refit all models on the full dataset and save as XGBoost JSON.

    Stage 1 models (color/pattern/symmetry) are refit on raw features,
    then predict the full dataset to build the stage-2 overall features.

    Args:
        datasets: Dataset DataFrames per pattern type.
        models_dir: Where to save <type>_<target>.json models.
        seed: Random seed.
    """
    models_dir.mkdir(parents=True, exist_ok=True)

    for pattern_type, df in datasets.items():
        if df.empty:
            logger.warning(f"Skipping {pattern_type}: empty dataset")
            continue

        X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
        stage1_models: dict[str, XGBRegressor] = {}
        stage1_preds: list[np.ndarray] = []

        for target in STAGE1_TARGETS:
            model = XGBRegressor(**XGB_PARAMS, random_state=seed)
            model.fit(X, df[target].to_numpy(dtype=float))
            stage1_models[target] = model
            stage1_preds.append(model.predict(X))
            model.save_model(str(models_dir / f"{pattern_type}_{target}.json"))

        overall_model = XGBRegressor(**XGB_PARAMS, random_state=seed)
        overall_model.fit(
            np.hstack([X, np.column_stack(stage1_preds)]),
            df[OVERALL_TARGET].to_numpy(dtype=float),
        )
        overall_model.save_model(str(models_dir / f"{pattern_type}_{OVERALL_TARGET}.json"))

        logger.info(
            f"Saved {len(stage1_models) + 1} models for {pattern_type} to {models_dir}"
        )

    metadata = {
        "feature_columns": FEATURE_COLUMNS,
        "targets": EXPERT_TARGETS,
        "stage1_targets": STAGE1_TARGETS,
        "overall_target": OVERALL_TARGET,
        "score_min": EXPERT_SCORE_MIN,
        "score_max": EXPERT_SCORE_MAX,
        "types": sorted(datasets.keys()),
    }
    with open(models_dir / "features.json", "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Model metadata written to {models_dir / 'features.json'}")


# =============================================================================
# CLI
# =============================================================================


def _parse_csvs(raw: str) -> dict[str, Path]:
    """Parse 'type:path,type:path' CLI argument into a mapping."""
    csvs: dict[str, Path] = {}
    for pair in raw.split(","):
        pattern_type, _, path = pair.strip().partition(":")
        if pattern_type not in KOI_PATTERNS:
            raise ValueError(f"Unknown pattern type '{pattern_type}'. Use: {KOI_PATTERNS}")
        csvs[pattern_type] = Path(path)
    return csvs


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Train expert-scoring XGBoost models.")
    parser.add_argument(
        "--csvs",
        required=True,
        help='Expert ratings CSVs as "type:path" pairs, comma-separated, e.g. '
        '"sanke:training/sanke.csv,kohaku:training/kohaku.csv,ogon:training/ogon.csv"',
    )
    parser.add_argument(
        "--images-root",
        type=Path,
        default=Path("./training"),
        help="Root dir with one image subfolder per pattern type (default: ./training)",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=None,
        help="Where intermediate dataset CSVs are saved (default: <images-root>/datasets)",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Where metrics and confusion matrices are saved (default: <images-root>/results)",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=EXPERT_MODEL_DIR,
        help="Where production models are saved (default: ./models/expert)",
    )
    parser.add_argument("--folds", type=int, default=5, help="CV folds (default: 5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument(
        "--skip-features",
        action="store_true",
        help="Reuse existing dataset CSVs instead of re-extracting features",
    )
    parser.add_argument(
        "--features-only",
        action="store_true",
        help="Only build datasets, skip training and model saving",
    )
    parser.add_argument(
        "--train-only",
        action="store_true",
        help="Only train from existing dataset CSVs (implies --skip-features)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    csvs = _parse_csvs(args.csvs)
    if args.train_only:
        args.skip_features = True

    # Datasets and results live next to the images, not the CWD
    if args.dataset_dir is None:
        args.dataset_dir = args.images_root / "datasets"
    if args.results_dir is None:
        args.results_dir = args.images_root / "results"

    datasets = load_datasets(
        csvs=csvs,
        images_root=args.images_root,
        dataset_dir=args.dataset_dir,
        skip_features=args.skip_features,
    )

    if args.features_only:
        logger.info("Feature extraction complete. Datasets ready for training.")
        return

    oof_by_type: dict[str, pd.DataFrame] = {}
    for pattern_type, df in datasets.items():
        if df.empty:
            logger.warning(f"Skipping training for {pattern_type}: empty dataset")
            continue
        oof_by_type[pattern_type] = train_type(df, args.folds, args.seed)

    if not oof_by_type:
        raise SystemExit("No datasets available for training")

    pooled_oof = pd.concat(oof_by_type.values(), ignore_index=True)

    args.results_dir.mkdir(parents=True, exist_ok=True)
    pooled_oof.to_csv(args.results_dir / "predictions_oof.csv", index=False)
    metrics = evaluate(oof_by_type)
    metrics.to_csv(args.results_dir / "metrics.csv", index=False)
    write_confusion_matrices(pooled_oof, args.results_dir)
    logger.info(f"Metrics and confusion matrices written to {args.results_dir}")

    refit_production_models(datasets, args.models_dir, args.seed)


if __name__ == "__main__":
    main()
