import React, { useState, useEffect } from 'react';

interface PredictionAnalysisProps {
  daysBack?: number;
  season?: number;
  matchday?: number;
}

interface AnalysisData {
  total_matches: number;
  overall_accuracy: number;
  average_log_loss: number;
  error_distribution: {
    correct_predictions: number;
    incorrect_predictions: number;
  };
  outcome_analysis: {
    home_wins: number;
    draws: number;
    away_wins: number;
  };
  confidence_analysis: {
    high_confidence_errors: number;
    low_confidence_correct: number;
    average_confidence: number;
  };
  worst_predictions: Array<{
    match_id: number;
    log_loss_error: number;
    confidence: number;
    accuracy: number;
  }>;
  best_predictions: Array<{
    match_id: number;
    log_loss_error: number;
    confidence: number;
    accuracy: number;
  }>;
}

const PredictionAnalysis: React.FC<PredictionAnalysisProps> = ({ 
  daysBack = 7, 
  season, 
  matchday 
}) => {
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retraining, setRetraining] = useState(false);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let url = `http://localhost:8000/ml/analysis?days_back=${daysBack}`;
      if (season) url += `&season=${season}`;
      if (matchday) url += `&matchday=${matchday}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analysis');
    } finally {
      setLoading(false);
    }
  };

  const retrainModel = async () => {
    setRetraining(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/ml/retrain?algorithm=xgb&days_back=30&error_weighting=true', {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      alert(`Model retrained successfully! New accuracy: ${(result.metrics.val_accuracy * 100).toFixed(1)}%`);
      
      // Refresh analysis
      fetchAnalysis();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrain model');
    } finally {
      setRetraining(false);
    }
  };

  useEffect(() => {
    fetchAnalysis();
  }, [daysBack, season, matchday]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span className="text-red-800">Error: {error}</span>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-900">Prediction Analysis</h2>
        <button
          onClick={retrainModel}
          disabled={retraining}
          className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors"
        >
          {retraining ? 'Retraining...' : 'Retrain Model'}
        </button>
      </div>

      {/* Overall Performance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-blue-800">Total Matches</h3>
          <p className="text-2xl font-bold text-blue-900">{analysis.total_matches}</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-green-800">Accuracy</h3>
          <p className="text-2xl font-bold text-green-900">
            {(analysis.overall_accuracy * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-purple-800">Log Loss</h3>
          <p className="text-2xl font-bold text-purple-900">
            {analysis.average_log_loss.toFixed(4)}
          </p>
        </div>
      </div>

      {/* Prediction Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <h3 className="text-lg font-semibold mb-3">Prediction Results</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-green-600">✅ Correct</span>
              <span className="font-semibold">{analysis.error_distribution.correct_predictions}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-red-600">❌ Incorrect</span>
              <span className="font-semibold">{analysis.error_distribution.incorrect_predictions}</span>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-3">Actual Outcomes</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>🏠 Home Wins</span>
              <span className="font-semibold">{analysis.outcome_analysis.home_wins}</span>
            </div>
            <div className="flex justify-between">
              <span>🤝 Draws</span>
              <span className="font-semibold">{analysis.outcome_analysis.draws}</span>
            </div>
            <div className="flex justify-between">
              <span>✈️ Away Wins</span>
              <span className="font-semibold">{analysis.outcome_analysis.away_wins}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Confidence Analysis */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Confidence Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <p className="text-sm text-red-600">High Confidence Errors</p>
            <p className="text-xl font-bold text-red-900">{analysis.confidence_analysis.high_confidence_errors}</p>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <p className="text-sm text-green-600">Low Confidence Correct</p>
            <p className="text-xl font-bold text-green-900">{analysis.confidence_analysis.low_confidence_correct}</p>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-600">Avg Confidence</p>
            <p className="text-xl font-bold text-blue-900">
              {(analysis.confidence_analysis.average_confidence * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Worst Predictions */}
      {analysis.worst_predictions.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">🔥 Worst Predictions</h3>
          <div className="space-y-2">
            {analysis.worst_predictions.slice(0, 5).map((pred, index) => (
              <div key={index} className="flex justify-between items-center p-2 bg-red-50 rounded">
                <span className="text-sm">Match {pred.match_id}</span>
                <div className="flex space-x-4 text-sm">
                  <span>Loss: {pred.log_loss_error.toFixed(4)}</span>
                  <span>Conf: {(pred.confidence * 100).toFixed(1)}%</span>
                  <span>{pred.accuracy ? '✅' : '❌'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Best Predictions */}
      {analysis.best_predictions.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">⭐ Best Predictions</h3>
          <div className="space-y-2">
            {analysis.best_predictions.slice(0, 5).map((pred, index) => (
              <div key={index} className="flex justify-between items-center p-2 bg-green-50 rounded">
                <span className="text-sm">Match {pred.match_id}</span>
                <div className="flex space-x-4 text-sm">
                  <span>Loss: {pred.log_loss_error.toFixed(4)}</span>
                  <span>Conf: {(pred.confidence * 100).toFixed(1)}%</span>
                  <span>{pred.accuracy ? '✅' : '❌'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictionAnalysis;
