# Feature 4: Results Display & Export

**Status:** � Completed  
**Last Updated:** 2026-02-05

---

## Overview

Display the koi fish appraisal results including individual metrics, price prediction, and a visualization of where the fish falls on the price regression model. Allow export of results to CSV.

---

## UI Components

### ResultsPanel Component

Displays after successful appraisal:

```typescript
interface AppraisalResult {
  size_cm: number;
  pattern: {
    name: string;
    confidence: number;
  };
  color: {
    white_pct: number;
    red_pct: number;
    black_pct: number;
    quality_score: number;
  };
  symmetry_score: number;
  predicted_price: number;
  image_url: string;
}
```

### Metrics Cards

Individual cards for each metric:

| Metric | Display |
|--------|---------|
| Size | "25.4 cm" with ruler icon |
| Pattern | "Kohaku" with pattern preview |
| Color | Pie chart of color distribution |
| Symmetry | Progress bar (0-100%) |
| Price | Large highlighted price value |

### Regression Graph

Interactive scatter plot showing:
- X-axis: Combined feature score (or selectable metric)
- Y-axis: Price
- Training data points (gray)
- Current fish point (highlighted)
- Regression line
- Confidence interval band

**Library:** Recharts or Chart.js

---

## Layout

```
┌─────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │             │  │     PREDICTED PRICE         │  │
│  │   Image     │  │       ₱ 85,000             │  │
│  │   Preview   │  │                             │  │
│  │             │  └─────────────────────────────┘  │
│  └─────────────┘                                   │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │   Size   │ │ Pattern  │ │  Color   │ │Symmetry││
│  │  25.4cm  │ │  Kohaku  │ │  [pie]   │ │  87%   ││
│  └──────────┘ └──────────┘ └──────────┘ └────────┘│
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │          Regression Graph                    │   │
│  │    •  •    •                                │   │
│  │      •  ★•   •    <- current fish          │   │
│  │   •    •  •                                 │   │
│  │  ─────────────────────                      │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  [ Export to CSV ]  [ New Capture ]                │
└─────────────────────────────────────────────────────┘
```

---

## Export Functionality

### CSV Export

Export current appraisal or batch of appraisals:

```csv
timestamp,image_name,size_cm,pattern,color_white,color_red,color_black,color_quality,symmetry,predicted_price
2026-02-05T10:30:00Z,capture_001.jpg,25.4,kohaku,45.2,38.1,16.7,0.85,0.87,85000
```

### Export Options
- Single result export
- Batch export (if multiple captures in session)
- Include/exclude image file option

---

## Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/components/ResultsPanel.tsx` | Main results container |
| `frontend/src/components/MetricCard.tsx` | Individual metric display |
| `frontend/src/components/RegressionGraph.tsx` | Price regression visualization |
| `frontend/src/components/ColorPieChart.tsx` | Color distribution chart |
| `frontend/src/utils/exportCsv.ts` | CSV export utility |

---

## State Management

```typescript
interface AppState {
  capturedImage: Blob | null;
  appraisalResult: AppraisalResult | null;
  isLoading: boolean;
  error: Error | null;
  history: AppraisalResult[]; // For batch export
}
```

---

## Animations

- Results cards fade in sequentially
- Price number counts up animation
- Graph points animate into position
- Loading skeleton while processing

---

## Responsive Design

**Desktop (>1024px):**
- Two-column layout (image left, metrics right)
- Full graph below

**Tablet (768-1024px):**
- Single column, stacked layout
- Scrollable metrics row

**Mobile (<768px):**
- Single column
- Collapsible metric details
- Swipeable graph

---

## Testing Checklist

- [ ] All metrics display correctly
- [ ] Regression graph renders with data
- [ ] Current point highlighted on graph
- [ ] CSV export produces valid file
- [ ] Responsive layout works
- [ ] Loading states display
- [ ] Error states display
- [ ] "New Capture" returns to camera

---

## Completion Checklist

When this feature is complete:
- [ ] Results panel implemented
- [ ] All metric cards implemented
- [ ] Regression graph working
- [ ] CSV export functional
- [ ] Responsive design complete
- [ ] Animations implemented
- [ ] Update status in FEATURES_INDEX.md to 🟢
