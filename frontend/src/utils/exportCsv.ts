/**
 * CSV Export Utility
 * 
 * Functions for exporting appraisal results to CSV.
 */

import type { AppraisalHistoryItem } from '../types';

/**
 * Convert appraisal history to CSV string
 */
export function toCSV(items: AppraisalHistoryItem[]): string {
    const headers = [
        'timestamp',
        'size_cm',
        'pattern',
        'pattern_confidence',
        'color_white_pct',
        'color_red_pct',
        'color_black_pct',
        'color_quality',
        'symmetry',
        'predicted_price',
    ];

    const rows = items.map(item => [
        item.timestamp.toISOString(),
        item.result.size_cm.toFixed(2),
        item.result.pattern_name,
        item.result.pattern_confidence.toFixed(3),
        item.result.color_white_pct.toFixed(1),
        item.result.color_red_pct.toFixed(1),
        item.result.color_black_pct.toFixed(1),
        item.result.color_quality_score.toFixed(3),
        item.result.symmetry_score.toFixed(3),
        item.result.predicted_price.toFixed(2),
    ]);

    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(',')),
    ].join('\n');

    return csvContent;
}

/**
 * Download CSV file
 */
export function downloadCSV(items: AppraisalHistoryItem[], filename?: string): void {
    const csv = toCSV(items);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `koi-appraisal-${new Date().toISOString().split('T')[0]}.csv`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
}
