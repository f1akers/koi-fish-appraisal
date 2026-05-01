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

## Overall Score

Derived from color and symmetry scores only:

```
overall_score = (color_score + symmetry_score) / 2
```

**Range:** 0–1
