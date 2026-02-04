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
    <div className="min-h-screen bg-white">
      {/* Header - Flat design with gradient accent */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Logo with gradient background */}
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                <span className="text-xl">🐟</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Koi Appraisal</h1>
                <p className="text-xs text-gray-500">AI-Powered Fish Valuation</p>
              </div>
            </div>

            {/* Session counter badge */}
            {history.length > 0 && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-violet-50 to-purple-50 rounded-full">
                <div className="w-2 h-2 rounded-full bg-gradient-to-r from-violet-500 to-purple-600"></div>
                <span className="text-sm font-medium text-purple-700">
                  {history.length} appraisal{history.length !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 pb-24">
        {/* Error Banner - Flat design */}
        {error && (
          <div className="mb-8 p-5 bg-gradient-to-r from-red-50 to-rose-50 border border-red-100 rounded-2xl">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-400 to-rose-500 flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="font-semibold text-red-800">Something went wrong</p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Camera View */}
        {view === 'camera' && (
          <div className="animate-fade-in">
            <CameraCapture onCapture={handleCapture} isProcessing={isLoading} />
          </div>
        )}

        {/* Results View */}
        {view === 'results' && result && (
          <div className="animate-fade-in">
            <ResultsPanel
              result={result}
              imagePreview={imagePreview}
              onNewCapture={handleNewCapture}
              onExport={handleExport}
            />
          </div>
        )}
      </main>

      {/* Footer - Minimal flat design */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-sm border-t border-gray-100 py-3">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
            <span>Powered by</span>
            <span className="font-semibold bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
              YOLOv8 + Linear Regression
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
