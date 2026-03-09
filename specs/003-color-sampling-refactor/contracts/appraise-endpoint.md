# API Contract: POST /api/appraise (Updated)

**Spec**: [../spec.md](../spec.md) | **Data Model**: [../data-model.md](../data-model.md)
**Date**: 2026-03-09

---

## Endpoint

```
POST /api/appraise
Content-Type: multipart/form-data
```

## Request

### Form Fields

| Field   | Type | Required | Description                  |
| ------- | ---- | -------- | ---------------------------- |
| `image` | File | Yes      | Image file (JPEG, PNG, etc.) |

### Validation Rules

- `Content-Type` header must indicate an image MIME type (`image/*`).
- File must be decodable by OpenCV (`cv2.imdecode`).

---

## Response (200 OK)

### Schema: `AppraisalResponse`

```json
{
  "size_cm": 25.4,
  "pattern_name": "kohaku",
  "pattern_confidence": 0.92,
  "color_proportions": {
    "Red": 42.3,
    "White": 35.1,
    "Black": 22.6
  },
  "symmetry_score": 0.87
}
```

### Field Definitions

| Field                | Type               | Constraints      | Description                                        |
| -------------------- | ------------------ | ---------------- | -------------------------------------------------- |
| `size_cm`            | `float`            | ≥ 0              | Fish size in cm (median of N inference samples)    |
| `pattern_name`       | `string`           | non-empty        | Detected pattern name (majority vote of N samples) |
| `pattern_confidence` | `float`            | 0.0–1.0          | Mean confidence of winning pattern votes           |
| `color_proportions`  | `Dict[str, float]` | values 0.0–100.0 | Named color → percentage. Keys vary per image.     |
| `symmetry_score`     | `float`            | 0.0–1.0          | Bilateral symmetry score (1.0 = perfect)           |

### Color Proportions Detail

- Keys are named koi colors: `"White"`, `"Red"`, `"Black"`, `"Orange"`, `"Yellow"`, `"Other"`
- Only colors with > 0% presence are included
- Values sum to ~100% (±1% rounding tolerance)
- At minimum 1 key, at maximum 6 keys (5 named + Other)

---

## Error Responses

| Status | Condition                            | Response Body                                                   |
| ------ | ------------------------------------ | --------------------------------------------------------------- |
| 400    | Invalid file type (not image)        | `{"detail": "Invalid file type. Please upload an image file."}` |
| 422    | Size detection failed (no fish/coin) | `{"detail": "Size detection failed: {reason}"}`                 |
| 503    | ML model file missing                | `{"detail": "Model not available: {model_name}"}`               |
| 500    | Unexpected processing error          | `{"detail": "Error processing image: {message}"}`               |

---

## Removed Fields (vs. previous version)

The following fields are **no longer returned**:

| Field                 | Reason                                    |
| --------------------- | ----------------------------------------- |
| `color_white_pct`     | Replaced by `color_proportions["White"]`  |
| `color_red_pct`       | Replaced by `color_proportions["Red"]`    |
| `color_black_pct`     | Replaced by `color_proportions["Black"]`  |
| `color_quality_score` | No equivalent in new clustering approach  |
| `predicted_price`     | Price prediction feature removed (FR-005) |

---

## Removed Endpoints

| Endpoint          | Reason                                |
| ----------------- | ------------------------------------- |
| `POST /api/train` | Price model training removed (FR-005) |

---

## Backward Compatibility

**This is a BREAKING CHANGE.** Frontend must be updated simultaneously.

- `color_proportions` (dict) replaces 4 fixed color fields
- `predicted_price` is removed entirely
- Clients parsing the old flat color fields will fail
- The `/api/train` endpoint will return 404
