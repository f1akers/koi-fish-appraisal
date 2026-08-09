/**
 * CSV Export Utility
 *
 * Functions for exporting appraisal results to CSV.
 */

import type { AppraisalHistoryItem } from "../types";

/**
 * Convert appraisal history to CSV string
 */
export function toCSV(items: AppraisalHistoryItem[]): string {
  // Collect all unique color keys across all items
  const colorKeys = new Set<string>();
  for (const item of items) {
    for (const key of Object.keys(item.result.color_proportions)) {
      colorKeys.add(key);
    }
  }
  const sortedColorKeys = Array.from(colorKeys).sort();

  const headers = [
    "timestamp",
    "size_cm",
    "pattern",
    "pattern_confidence",
    "pattern_score",
    ...sortedColorKeys.map((k) => `color_${k.toLowerCase()}_pct`),
    "symmetry",
    "color_score",
    "overall_score",
    "scoring_mode",
  ];

  const rows = items.map((item) => [
    item.timestamp.toISOString(),
    item.result.size_cm.toFixed(2),
    item.result.pattern_name,
    item.result.pattern_confidence.toFixed(3),
    item.result.pattern_score.toFixed(3),
    ...sortedColorKeys.map((k) =>
      (item.result.color_proportions[k] ?? 0).toFixed(1),
    ),
    item.result.symmetry_score.toFixed(3),
    item.result.color_score.toFixed(3),
    item.result.overall_score.toFixed(3),
    item.result.scoring_mode,
  ]);

  const csvContent = [
    headers.join(","),
    ...rows.map((row) => row.join(",")),
  ].join("\n");

  return csvContent;
}

/**
 * Download CSV file
 */
export function downloadCSV(
  items: AppraisalHistoryItem[],
  filename?: string,
): void {
  const csv = toCSV(items);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download =
    filename || `koi-appraisal-${new Date().toISOString().split("T")[0]}.csv`;

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}
