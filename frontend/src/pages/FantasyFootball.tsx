import React, { useState } from 'react';
import FantasyFootballAgent from '../components/FantasyFootballAgent';
import { Calculator, Settings, HelpCircle, Brain, Zap, Target } from 'lucide-react';

const FantasyFootball: React.FC = () => {
  const [budget, setBudget] = useState<number>(2.0);
  const [analysisTypes, setAnalysisTypes] = useState<string[]>(['transfers', 'captain', 'differential']);
  const [gameweeksAhead, setGameweeksAhead] = useState<number>(5);
  const [showSettings, setShowSettings] = useState<boolean>(false);

  const handleAnalysisTypeChange = (type: string, checked: boolean) => {
    if (checked) {
      setAnalysisTypes(prev => [...prev, type]);
    } else {
      setAnalysisTypes(prev => prev.filter(t => t !== type));
    }
  };

  const analysisOptions = [
    { id: 'transfers', label: 'AI Transfer Recommendations', description: 'Machine learning-powered transfer suggestions' },
    { id: 'captain', label: 'AI Captain Analysis', description: 'Predictive captain selection using ML models' },
    { id: 'differential', label: 'AI Differential Picks', description: 'Low-owned players with high AI-predicted potential' }
  ];

  return (
    <div className="pt-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">AI Fantasy Football Assistant</h1>
            <p className="text-gray-600 mt-2">
              Machine learning-powered analysis to dominate your Fantasy Premier League
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="flex items-center bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md transition-colors"
            >
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </button>
            
            <div className="relative">
              <button className="flex items-center bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-2 rounded-md transition-colors">
                <HelpCircle className="w-4 h-4 mr-2" />
                Help
              </button>
            </div>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6 border">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Calculator className="w-5 h-5 mr-2 text-blue-600" />
              AI Analysis Settings
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Budget Setting */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Transfer Budget
                </label>
                <div className="flex items-center">
                  <span className="text-gray-500 mr-2">£</span>
                  <input
                    type="number"
                    min="0"
                    max="20"
                    step="0.1"
                    value={budget}
                    onChange={(e) => setBudget(parseFloat(e.target.value))}
                    className="border border-gray-300 rounded-md px-3 py-2 w-24 text-center"
                  />
                  <span className="text-gray-500 ml-2">million</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Available budget for transfers
                </p>
              </div>

              {/* Gameweeks Setting */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Gameweeks to Analyze
                </label>
                <select
                  value={gameweeksAhead}
                  onChange={(e) => setGameweeksAhead(parseInt(e.target.value))}
                  className="border border-gray-300 rounded-md px-3 py-2 w-full"
                >
                  <option value={1}>Next 1 gameweek</option>
                  <option value={3}>Next 3 gameweeks</option>
                  <option value={5}>Next 5 gameweeks</option>
                  <option value={10}>Next 10 gameweeks</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  How far ahead to plan your strategy
                </p>
              </div>

              {/* Analysis Types */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Analysis Types
                </label>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {analysisOptions.map(option => (
                    <label key={option.id} className="flex items-start">
                      <input
                        type="checkbox"
                        checked={analysisTypes.includes(option.id)}
                        onChange={(e) => handleAnalysisTypeChange(option.id, e.target.checked)}
                        className="mt-1 mr-2"
                      />
                      <div className="text-sm">
                        <div className="font-medium text-gray-900">{option.label}</div>
                        <div className="text-gray-500">{option.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t flex justify-end">
              <button
                onClick={() => setShowSettings(false)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
              >
                Apply Settings
              </button>
            </div>
          </div>
        )}

        {/* AI Features Highlight */}
        {/* <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 mb-6 border border-purple-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <Brain className="w-5 h-5 text-purple-600 mr-2" />
            AI-Powered Features
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-start">
              <Zap className="w-4 h-4 text-green-600 mr-2 mt-0.5" />
              <div>
                <strong className="text-green-700">ML Predictions:</strong>
                <p className="text-gray-600">Trained on 5 seasons of data for accurate player performance forecasts</p>
              </div>
            </div>
            <div className="flex items-start">
              <Target className="w-4 h-4 text-blue-600 mr-2 mt-0.5" />
              <div>
                <strong className="text-blue-700">Personalized Analysis:</strong>
                <p className="text-gray-600">Get recommendations based on your current team and budget</p>
              </div>
            </div>
            <div className="flex items-start">
              <Brain className="w-4 h-4 text-purple-600 mr-2 mt-0.5" />
              <div>
                <strong className="text-purple-700">Risk Assessment:</strong>
                <p className="text-gray-600">AI evaluates risk levels and confidence scores for every recommendation</p>
              </div>
            </div>
          </div>
        </div> */}

        {/* Main Fantasy Agent Component */}
        <FantasyFootballAgent 
        />

        {/* Quick Actions */}
        {/* <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow-md p-6 border hover:shadow-lg transition-shadow">
            <h4 className="font-semibold text-gray-900 mb-2">🎯 AI Weekly Planner</h4>
            <p className="text-sm text-gray-600 mb-4">
              Get AI-powered transfer and captain recommendations for upcoming gameweeks
            </p>
            <button className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md transition-colors">
              View Planner
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border hover:shadow-lg transition-shadow">
            <h4 className="font-semibold text-gray-900 mb-2">📊 AI Team Analyzer</h4>
            <p className="text-sm text-gray-600 mb-4">
              Upload your current team for personalized AI transfer recommendations
            </p>
            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md transition-colors">
              Analyze Team
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border hover:shadow-lg transition-shadow">
            <h4 className="font-semibold text-gray-900 mb-2">🏆 AI League Tracker</h4>
            <p className="text-sm text-gray-600 mb-4">
              Track your performance with AI-powered insights and predictions
            </p>
            <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-md transition-colors">
              Track League
            </button>
          </div>
        </div> */}

        {/* Footer Info */}
        {/* <div className="mt-12 bg-gray-50 rounded-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">How the AI Agent Works</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <p>• <strong>Machine Learning Models:</strong> Trained on 9 seasons of FPL data for accurate predictions</p>
                <p>• <strong>Real-time Data:</strong> Analyzes live FPL data including prices, ownership, and form</p>
                <p>• <strong>Feature Engineering:</strong> Advanced statistical features for better prediction accuracy</p>
                <p>• <strong>Risk Assessment:</strong> AI evaluates confidence levels and risk scores for every recommendation</p>
                <p>• <strong>Personalization:</strong> Tailored recommendations based on your team and budget</p>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">AI Data Sources & Models</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <p>• <strong>Historical Data:</strong> 9 seasons of player performance data (2016-2025)</p>
                <p>• <strong>ML Algorithms:</strong> Random Forest, Gradient Boosting, and XGBoost models</p>
                <p>• <strong>Real-time APIs:</strong> Official FPL API for current season data</p>
                <p>• <strong>Feature Analysis:</strong> Goals, assists, minutes, form, and value metrics</p>
              </div>
              
              <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-xs text-blue-800">
                  <strong>AI Disclaimer:</strong> This tool uses machine learning models trained on historical data. 
                  While predictions are based on statistical analysis, fantasy football involves uncertainty. 
                  Always make your own informed decisions.
                </p>
              </div>
            </div>
          </div>
        </div> */}
      </div>
    </div>
  );
};

export default FantasyFootball;