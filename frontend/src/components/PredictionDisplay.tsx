import React, { useState, useEffect } from 'react';

interface Prediction {
  matchId: number;
  homeTeam: string;
  awayTeam: string;
  probs: {
    home: number;
    draw: number;
    away: number;
  };
  model_version: string;
  note?: string;
}

interface PredictionDisplayProps {
  matchId: number;
  compact?: boolean;
}

const PredictionDisplay: React.FC<PredictionDisplayProps> = ({ matchId, compact = false }) => {
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrediction = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/ml/predict?match_id=${matchId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setPrediction(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch prediction');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (matchId) {
      fetchPrediction();
    }
  }, [matchId]);

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md ${compact ? 'p-3' : 'p-4'}`}>
        <div className="animate-pulse">
          {compact ? (
            <div className="flex space-x-2">
              <div className="h-6 bg-gray-200 rounded flex-1"></div>
              <div className="h-6 bg-gray-200 rounded flex-1"></div>
              <div className="h-6 bg-gray-200 rounded flex-1"></div>
            </div>
          ) : (
            <>
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="flex space-x-2">
                <div className="h-8 bg-gray-200 rounded flex-1"></div>
                <div className="h-8 bg-gray-200 rounded flex-1"></div>
                <div className="h-8 bg-gray-200 rounded flex-1"></div>
              </div>
            </>
          )}
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

  if (!prediction) {
    return null;
  }

  const getHighestProb = () => {
    const { home, draw, away } = prediction.probs;
    if (home > draw && home > away) return 'home';
    if (away > draw && away > home) return 'away';
    return 'draw';
  };

  const highestProb = getHighestProb();
  const confidence = Math.max(prediction.probs.home, prediction.probs.draw, prediction.probs.away);

  if (compact) {
    return (
      <div className="bg-white rounded-lg shadow-md p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-gray-700">AI Prediction</span>
          <span className={`text-xs font-bold px-2 py-1 rounded ${
            highestProb === 'home' ? 'bg-green-100 text-green-800' :
            highestProb === 'draw' ? 'bg-blue-100 text-blue-800' :
            'bg-red-100 text-red-800'
          }`}>
            {highestProb === 'home' ? 'H' :
             highestProb === 'draw' ? 'D' : 'A'}
          </span>
        </div>
        
        <div className="flex space-x-1">
          <div className="flex-1 text-center">
            <div className="text-xs text-gray-600">H</div>
            <div className="text-sm font-bold text-gray-900">
              {(prediction.probs.home * 100).toFixed(0)}%
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
              <div 
                className={`h-1 rounded-full ${highestProb === 'home' ? 'bg-green-500' : 'bg-gray-400'}`}
                style={{ width: `${prediction.probs.home * 100}%` }}
              ></div>
            </div>
          </div>
          
          <div className="flex-1 text-center">
            <div className="text-xs text-gray-600">D</div>
            <div className="text-sm font-bold text-gray-900">
              {(prediction.probs.draw * 100).toFixed(0)}%
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
              <div 
                className={`h-1 rounded-full ${highestProb === 'draw' ? 'bg-blue-500' : 'bg-gray-400'}`}
                style={{ width: `${prediction.probs.draw * 100}%` }}
              ></div>
            </div>
          </div>
          
          <div className="flex-1 text-center">
            <div className="text-xs text-gray-600">A</div>
            <div className="text-sm font-bold text-gray-900">
              {(prediction.probs.away * 100).toFixed(0)}%
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
              <div 
                className={`h-1 rounded-full ${highestProb === 'away' ? 'bg-red-500' : 'bg-gray-400'}`}
                style={{ width: `${prediction.probs.away * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-gray-900">AI Prediction</h3>
        <p className="text-sm text-gray-500">Model: {prediction.model_version}</p>
        {prediction.note && (
          <p className="text-xs text-amber-600 mt-1">{prediction.note}</p>
        )}
      </div>

      <div className="space-y-3">
        {/* Prediction Bars */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Home Win</span>
            <span className="text-sm font-bold text-gray-900">
              {(prediction.probs.home * 100).toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${highestProb === 'home' ? 'bg-green-500' : 'bg-gray-400'}`}
              style={{ width: `${prediction.probs.home * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Draw</span>
            <span className="text-sm font-bold text-gray-900">
              {(prediction.probs.draw * 100).toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${highestProb === 'draw' ? 'bg-blue-500' : 'bg-gray-400'}`}
              style={{ width: `${prediction.probs.draw * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Away Win</span>
            <span className="text-sm font-bold text-gray-900">
              {(prediction.probs.away * 100).toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${highestProb === 'away' ? 'bg-red-500' : 'bg-gray-400'}`}
              style={{ width: `${prediction.probs.away * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Prediction Summary */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Predicted Outcome:</span>
          <span className={`text-sm font-bold px-2 py-1 rounded ${
            highestProb === 'home' ? 'bg-green-100 text-green-800' :
            highestProb === 'draw' ? 'bg-blue-100 text-blue-800' :
            'bg-red-100 text-red-800'
          }`}>
            {highestProb === 'home' ? 'Home Win' :
             highestProb === 'draw' ? 'Draw' : 'Away Win'}
          </span>
        </div>
        <div className="mt-2">
          <span className="text-xs text-gray-500">
            Confidence: {(confidence * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Refresh Button */}
      <button
        onClick={fetchPrediction}
        className="mt-3 w-full bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium py-2 px-4 rounded-md transition-colors"
      >
        Refresh Prediction
      </button>
    </div>
  );
};

export default PredictionDisplay;
