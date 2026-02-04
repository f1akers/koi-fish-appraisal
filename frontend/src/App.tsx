/**
 * Koi Fish Appraisal Application
 */

import { useState, useCallback } from 'react';
import { CameraCapture, ResultsPanel } from './components';
import { appraiseImage } from './services/api';
import { downloadCSV } from './utils/exportCsv';
import type { AppraisalResult, AppraisalHistoryItem } from './types';

type AppView = 'camera' | 'results';

function App() {
  const [view, setView] = useState<AppView>('camera');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AppraisalResult | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [history, setHistory] = useState<AppraisalHistoryItem[]>([]);

  const handleCapture = useCallback(async (imageBlob: Blob) => {
    setIsLoading(true);
    setError(null);

    // Create preview URL
    const previewUrl = URL.createObjectURL(imageBlob);
    setImagePreview(previewUrl);

    try {
      const appraisalResult = await appraiseImage(imageBlob);
      setResult(appraisalResult);

      // Add to history
      const historyItem: AppraisalHistoryItem = {
        id: crypto.randomUUID(),
        timestamp: new Date(),
        imagePreview: previewUrl,
        result: appraisalResult,
      };
      setHistory(prev => [...prev, historyItem]);

      setView('results');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process image');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleNewCapture = useCallback(() => {
    setView('camera');
    setResult(null);
    setError(null);
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
      setImagePreview(null);
    }
  }, [imagePreview]);

  const handleExport = useCallback(() => {
    if (history.length > 0) {
      downloadCSV(history);
    }
  }, [history]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">🐟 Koi Fish Appraisal</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Camera View */}
        {view === 'camera' && (
          <CameraCapture onCapture={handleCapture} isProcessing={isLoading} />
        )}

        {/* Results View */}
        {view === 'results' && result && (
          <ResultsPanel
            result={result}
            imagePreview={imagePreview}
            onNewCapture={handleNewCapture}
            onExport={handleExport}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-2">
        <p className="text-center text-sm text-gray-500">
          {history.length} appraisal{history.length !== 1 ? 's' : ''} this session
        </p>
      </footer>
    </div>
  );
}

export default App;
