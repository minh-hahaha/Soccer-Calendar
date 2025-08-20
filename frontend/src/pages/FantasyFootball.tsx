import React, { useState } from 'react';
import FantasyFootballAgent from '../components/FantasyFootballAgent';
import { Calculator, Settings, HelpCircle } from 'lucide-react';

const FantasyFootball: React.FC = () => {
  const [budget, setBudget] = useState<number>(100.0);
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
    { id: 'transfers', label: 'Transfer Recommendations', description: 'Find the best players to bring in' },
    { id: 'captain', label: 'Captain Analysis', description: 'Identify top captain choices' },
    { id: 'differential', label: 'Differential Picks', description: 'Low-owned players with high potential' },
    { id: 'budget_optimization', label: 'Budget Optimization', description: 'Best ways to allocate your budget' },
    { id: 'fixture_planning', label: 'Fixture Planning', description: 'Plan transfers around fixture difficulty' }
  ];

  return (
    <div className="pt-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Fantasy Football Assistant</h1>
            <p className="text-gray-600 mt-2">
              AI-powered analysis to dominate your Fantasy Premier League
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
              Analysis Settings
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Budget Setting */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Available Budget
                </label>
                <div className="flex items-center">
                  <span className="text-gray-500 mr-2">£</span>
                  <input
                    type="number"
                    min="50"
                    max="120"
                    step="0.1"
                    value={budget}
                    onChange={(e) => setBudget(parseFloat(e.target.value))}
                    className="border border-gray-300 rounded-md px-3 py-2 w-24 text-center"
                  />
                  <span className="text-gray-500 ml-2">million</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Your current team value + money in the bank
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
                  Analysis Types
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

        {/* Quick Tips */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 mb-6 border border-blue-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">💡 Pro Tips from the AI Agent</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <strong className="text-blue-700">Transfer Timing:</strong>
              <p className="text-gray-600">Make transfers just before price rises to maximize team value</p>
            </div>
            <div>
              <strong className="text-green-700">Captain Strategy:</strong>
              <p className="text-gray-600">Consider fixture difficulty and recent form, not just big names</p>
            </div>
            <div>
              <strong className="text-purple-700">Differential Picks:</strong>
              <p className="text-gray-600">Low-owned players can give you a huge advantage in mini-leagues</p>
            </div>
          </div>
        </div>

        {/* Main Fantasy Agent Component */}
        <FantasyFootballAgent 
          budget={budget}
          analysisTypes={analysisTypes}
          gameweeksAhead={gameweeksAhead}
        />

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow-md p-6 border hover:shadow-lg transition-shadow">
            <h4 className="font-semibold text-gray-900 mb-2">🎯 Weekly Planner</h4>
            <p className="text-sm text-gray-600 mb-4">
              Plan your transfers and captain choices for the upcoming gameweeks
            </p>
            <button className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md transition-colors">
              View Planner
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border hover:shadow-lg transition-shadow">
            <h4 className="font-semibold text-gray-900 mb-2">📊 Team Analyzer</h4>
            <p className="text-sm text-gray-600 mb-4">
              Upload your current team for personalized transfer recommendations
            </p>
            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md transition-colors">
              Analyze Team
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border hover:shadow-lg transition-shadow">
            <h4 className="font-semibold text-gray-900 mb-2">🏆 League Tracker</h4>
            <p className="text-sm text-gray-600 mb-4">
              Track your performance against friends and global managers
            </p>
            <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-md transition-colors">
              Track League
            </button>
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-12 bg-gray-50 rounded-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">How the AI Agent Works</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <p>• <strong>Real-time Data:</strong> Analyzes live FPL data including prices, ownership, and form</p>
                <p>• <strong>Fixture Analysis:</strong> Considers upcoming opponents and difficulty ratings</p>
                <p>• <strong>Value Calculation:</strong> Finds players offering the best points per million</p>
                <p>• <strong>Market Trends:</strong> Tracks price changes and transfer trends</p>
                <p>• <strong>Strategic Planning:</strong> Optimizes for both short-term gains and long-term success</p>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Data Sources</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <p>• <strong>Official FPL API:</strong> Player stats, prices, and ownership data</p>
                <p>• <strong>Premier League API:</strong> Fixtures, results, and team performance</p>
                <p>• <strong>AI Analysis:</strong> Machine learning models for prediction and optimization</p>
                <p>• <strong>Market Intelligence:</strong> Transfer trends and price change predictions</p>
              </div>
              
              <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-xs text-blue-800">
                  <strong>Disclaimer:</strong> This tool provides analysis and suggestions based on data and algorithms. 
                  Fantasy football involves uncertainty and luck. Always make your own informed decisions.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FantasyFootball;