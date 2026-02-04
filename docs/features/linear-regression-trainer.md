# Feature 2: Linear Regression Trainer

**Status:** 🔴 Not Started  
**Last Updated:** -

---

## Overview

A training script that builds and saves a linear regression model for koi fish price prediction based on labeled training data.

---

## Input Requirements

### CSV File Format

| Column | Type | Description |
|--------|------|-------------|
| `image_filename` | string | Name of image file (must exist in `backend/images/`) |
| `price` | float | Appraised price of the koi fish |

**Example CSV:**
```csv
image_filename,price
koi_001.jpg,50000
koi_002.jpg,75000
koi_003.jpg,120000
```

### Image Storage
- All training images must be stored in `backend/images/`
- Supported formats: `.jpg`, `.jpeg`, `.png`
- Images should contain koi fish with reference coin visible

---

## Output

- Trained model saved to: `backend/models/linear.pkl`
- Training metrics logged to console
- Optional: Save training report to `backend/models/training_report.json`

---

## Implementation

### Training Pipeline

```python
def train_model(csv_path: str) -> None:
    """
    Train linear regression model from labeled data.
    
    Steps:
    1. Load CSV file
    2. For each image:
       a. Load image
       b. Extract all metrics (size, pattern, color, symmetry)
       c. Store feature vector with price label
    3. Split data into train/validation sets
    4. Train LinearRegression model
    5. Evaluate on validation set
    6. Save model to disk
    """
```

### Feature Vector

The feature vector for each image should include:
- `size_cm` - Fish size in centimeters
- `pattern_encoded` - One-hot encoded pattern (ogon, showa, kohaku)
- `color_white_pct` - Percentage of white
- `color_red_pct` - Percentage of red
- `color_black_pct` - Percentage of black
- `color_quality` - Overall color quality score
- `symmetry_score` - Bilateral symmetry score

---

## CLI Interface

```bash
# Train the model
python -m app.train --csv data/training_data.csv

# Train with custom output path
python -m app.train --csv data/training_data.csv --output models/custom_model.pkl

# Train with validation split
python -m app.train --csv data/training_data.csv --val-split 0.2
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `backend/app/train.py` | Main training script |
| `backend/app/utils/feature_extraction.py` | Extract features from image |

---

## Evaluation Metrics

The training script should output:
- R² Score
- Mean Absolute Error (MAE)
- Mean Squared Error (MSE)
- Root Mean Squared Error (RMSE)

---

## Testing Checklist

- [ ] CSV parsing handles edge cases (missing files, invalid data)
- [ ] Feature extraction is consistent with appraisal pipeline
- [ ] Model saves and loads correctly
- [ ] Training works with small dataset
- [ ] Validation metrics are calculated correctly

---

## Completion Checklist

When this feature is complete:
- [ ] Training script implemented and tested
- [ ] CLI interface working
- [ ] Documentation for CSV format
- [ ] Sample CSV provided for testing
- [ ] Update status in FEATURES_INDEX.md to 🟢
