import React, { useState, useEffect } from 'react';
import { 
  Trophy, TrendingUp, Users, Target, DollarSign, 
  Star, Zap, RefreshCw, AlertTriangle, Crown,
  ArrowUpRight, ArrowDownRight, Eye, Calculator
} from 'lucide-react';

interface TransferSuggestion {
  player_out: string;
  player_in: string;
  reason: string;
  priority: string;
  points_potential: number;
  risk_level: string;
  cost: number;
  confidence: number;
}

interface CaptainSuggestion {
  player: string;
  team: string;
  opponent: string;
  is_home: boolean;
  expected_points: number;
  ceiling: number;
  floor: number;
  reasoning: string;
  confidence: number;
  differential_factor: number;
}

interface DifferentialPick {
  name: string;
  team: string;
  position: string;
  price: number;
  ownership: number;
  form: number;
  value_score: number;
  reasoning: string;
  risk_level: string;
}

interface MarketInsights {
  price_changes: Array<{
    name: string;
    team: string;
    change: number;
    new_price: number;
    selected_by: number;
  }>;
  transfers_in: Array<any>;
  transfers_out: Array<any>;
  top_scorers: Array<any>;
}

interface FantasyAnalysis {
  gameweek: number;
  analysis_timestamp: string;
  budget: number;
  gameweeks_analyzed: number;
  recommendations: {
    transfers?: TransferSuggestion[];
    captain?: CaptainSuggestion[];
    differentials?: DifferentialPick[];
    budget?: any;
    fixtures?: any;
  };
  market_insights: MarketInsights;
  agent_summary: string;
}

interface FantasyAgentProps {
  budget?: number;
  analysisTypes?: string[];
  gameweeksAhead?: number;
}

const FantasyFootballAgent: React.FC<FantasyAgentProps> = ({ 
  budget = 100.0, 
  analysisTypes = ['transfers', 'captain', 'differential'],
  gameweeksAhead = 5 
}) => {
  const [analysis, setAnalysis] = useState<FantasyAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [refreshing, setRefreshing] = useState(false);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const analysisTypesStr = analysisTypes.join(',');
      const response = await fetch(
        `http://localhost:8000/fantasy/analyze?analysis_types=${analysisTypesStr}&budget=${budget}&gameweeks_ahead=${gameweeksAhead}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch fantasy analysis');
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await fetchAnalysis();
    setRefreshing(false);
  };

  useEffect(() => {
    fetchAnalysis();
  }, [budget, analysisTypes, gameweeksAhead]);

  const getPriorityColor = (priority: string) => {
    switch (priority.toUpperCase()) {
      case 'HIGH': return 'text-red-700 bg-red-100';
      case 'MEDIUM': return 'text-yellow-700 bg-yellow-100';
      case 'LOW': return 'text-green-700 bg-green-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk.toUpperCase()) {
      case 'HIGH': return 'text-red-600';
      case 'MEDIUM': return 'text-yellow-600';
      case 'LOW': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getPositionColor = (position: string) => {
    switch (position) {
      case 'Goalkeeper': return 'text-yellow-700 bg-yellow-100';
      case 'Defender': return 'text-blue-700 bg-blue-100';
      case 'Midfielder': return 'text-green-700 bg-green-100';
      case 'Forward': return 'text-red-700 bg-red-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  const formatCurrency = (amount: number) => `£${amount.toFixed(1)}m`;

  const formatPercentage = (value: number) => `${value.toFixed(1)}%`;

  const tabs = [
    { id: 'overview', name: 'Overview', icon: Trophy },
    { id: 'transfers', name: 'Transfers', icon: RefreshCw },
    { id: 'captain', name: 'Captain', icon: Crown },
    { id: 'differentials', name: 'Differentials', icon: Star },
    { id: 'market', name: 'Market', icon: TrendingUp }
  ];

  if (loading && !analysis) {
    return (
      <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg shadow-lg p-8">
        <div className="animate-pulse">
          <div className="flex items-center mb-6">
            <Trophy className="w-8 h-8 text-green-600 mr-3" />
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-white rounded-lg p-4">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <AlertTriangle className="w-6 h-6 text-red-500 mr-3" />
          <h3 className="text-lg font-semibold text-red-800">Fantasy Agent Error</h3>
        </div>
        <p className="text-red-700 mb-4">{error}</p>
        <button
          onClick={fetchAnalysis}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md transition-colors"
        >
          Retry Analysis
        </button>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Trophy className="w-8 h-8 text-green-600 mr-3" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Fantasy Football Agent</h1>
            <p className="text-sm text-gray-600">
              Gameweek {analysis.gameweek} • Budget: {formatCurrency(analysis.budget)}
            </p>
          </div>
        </div>
        <button
          onClick={refreshData}
          disabled={refreshing}
          className="flex items-center bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg p-4 border border-green-100">
              <div className="flex items-center">
                <Target className="w-5 h-5 text-green-600 mr-2" />
                <span className="text-sm font-medium text-gray-600">Transfer Targets</span>
              </div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {analysis.recommendations.transfers?.length || 0}
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4 border border-blue-100">
              <div className="flex items-center">
                <Crown className="w-5 h-5 text-blue-600 mr-2" />
                <span className="text-sm font-medium text-gray-600">Captain Options</span>
              </div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {analysis.recommendations.captain?.length || 0}
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4 border border-purple-100">
              <div className="flex items-center">
                <Star className="w-5 h-5 text-purple-600 mr-2" />
                <span className="text-sm font-medium text-gray-600">Differentials</span>
              </div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {analysis.recommendations.differentials?.length || 0}
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4 border border-orange-100">
              <div className="flex items-center">
                <TrendingUp className="w-5 h-5 text-orange-600 mr-2" />
                <span className="text-sm font-medium text-gray-600">Price Changes</span>
              </div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {analysis.market_insights.price_changes?.length || 0}
              </div>
            </div>
          </div>

          {/* Agent Summary */}
          <div className="bg-white rounded-lg p-6 border border-green-100">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Zap className="w-5 h-5 text-green-600 mr-2" />
              AI Agent Summary
            </h3>
            <div className="prose prose-sm max-w-none">
              <div className="whitespace-pre-line text-gray-700">
                {analysis.agent_summary}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'transfers' && analysis.recommendations.transfers && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">Transfer Recommendations</h3>
            <span className="text-sm text-gray-600">
              {analysis.recommendations.transfers.length} targets identified
            </span>
          </div>
          
          {analysis.recommendations.transfers.map((transfer, index) => (
            <div key={index} className="bg-white rounded-lg p-5 border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <h4 className="font-semibold text-lg text-gray-900 mr-3">
                      {transfer.player_in}
                    </h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(transfer.priority)}`}>
                      {transfer.priority}
                    </span>
                  </div>
                  <p className="text-gray-600 mb-3">{transfer.reason}</p>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-gray-900">
                    {formatCurrency(transfer.cost)}
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatPercentage(transfer.confidence * 100)} confidence
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Points Potential:</span>
                  <div className="font-semibold">{transfer.points_potential} pts</div>
                </div>
                <div>
                  <span className="text-gray-500">Risk Level:</span>
                  <div className={`font-semibold ${getRiskColor(transfer.risk_level)}`}>
                    {transfer.risk_level}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Confidence:</span>
                  <div className="font-semibold">{formatPercentage(transfer.confidence * 100)}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'captain' && analysis.recommendations.captain && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">Captain Analysis</h3>
            <span className="text-sm text-gray-600">
              Next {analysis.gameweeks_analyzed} gameweeks
            </span>
          </div>
          
          {analysis.recommendations.captain.map((captain, index) => (
            <div key={index} className="bg-white rounded-lg p-5 border border-gray-200">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <Crown className="w-5 h-5 text-yellow-500 mr-2" />
                    <h4 className="font-semibold text-lg text-gray-900">
                      {captain.player}
                    </h4>
                    <span className="ml-2 text-sm text-gray-600">
                      ({captain.team})
                    </span>
                  </div>
                  <div className="flex items-center text-sm text-gray-600 mb-2">
                    <span>vs {captain.opponent}</span>
                    <span className="mx-2">•</span>
                    <span>{captain.is_home ? '🏠 Home' : '✈️ Away'}</span>
                  </div>
                  <p className="text-gray-600">{captain.reasoning}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-green-600 font-medium">Expected</div>
                  <div className="text-lg font-bold text-green-800">
                    {captain.expected_points.toFixed(1)} pts
                  </div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-blue-600 font-medium">Ceiling</div>
                  <div className="text-lg font-bold text-blue-800">
                    {captain.ceiling.toFixed(1)} pts
                  </div>
                </div>
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <div className="text-red-600 font-medium">Floor</div>
                  <div className="text-lg font-bold text-red-800">
                    {captain.floor.toFixed(1)} pts
                  </div>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <div className="text-purple-600 font-medium">Confidence</div>
                  <div className="text-lg font-bold text-purple-800">
                    {formatPercentage(captain.confidence * 100)}
                  </div>
                </div>
              </div>
              
              {captain.differential_factor > 0.3 && (
                <div className="mt-3 p-2 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="flex items-center text-sm text-yellow-800">
                    <Eye className="w-4 h-4 mr-2" />
                    <span>Differential pick - lower ownership could give you an edge!</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'differentials' && analysis.recommendations.differentials && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">Differential Picks</h3>
            <span className="text-sm text-gray-600">
              Low ownership gems
            </span>
          </div>
          
          {analysis.recommendations.differentials.map((diff, index) => (
            <div key={index} className="bg-white rounded-lg p-5 border border-gray-200">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <h4 className="font-semibold text-lg text-gray-900 mr-3">
                      {diff.name}
                    </h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPositionColor(diff.position)}`}>
                      {diff.position}
                    </span>
                  </div>
                  <div className="flex items-center text-sm text-gray-600 mb-2">
                    <span>{diff.team}</span>
                    <span className="mx-2">•</span>
                    <span>{formatCurrency(diff.price)}</span>
                  </div>
                  <p className="text-gray-600">{diff.reasoning}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Ownership:</span>
                  <div className="font-semibold text-blue-600">
                    {formatPercentage(diff.ownership)}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Form:</span>
                  <div className="font-semibold text-green-600">
                    {diff.form.toFixed(1)}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Value Score:</span>
                  <div className="font-semibold text-purple-600">
                    {diff.value_score.toFixed(1)}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Risk:</span>
                  <div className={`font-semibold ${getRiskColor(diff.risk_level)}`}>
                    {diff.risk_level}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'market' && (
        <div className="space-y-6">
          <h3 className="text-xl font-semibold">Market Watch</h3>
          
          {/* Price Changes */}
          {analysis.market_insights.price_changes && analysis.market_insights.price_changes.length > 0 && (
            <div className="bg-white rounded-lg p-5 border border-gray-200">
              <h4 className="font-semibold mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 text-orange-600 mr-2" />
                Recent Price Changes
              </h4>
              <div className="space-y-3">
                {analysis.market_insights.price_changes.slice(0, 8).map((change, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <div className={`p-1 rounded-full mr-3 ${change.change > 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                        {change.change > 0 ? (
                          <ArrowUpRight className="w-4 h-4 text-green-600" />
                        ) : (
                          <ArrowDownRight className="w-4 h-4 text-red-600" />
                        )}
                      </div>
                      <div>
                        <div className="font-medium">{change.name}</div>
                        <div className="text-sm text-gray-600">{change.team}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">
                        {formatCurrency(change.new_price)}
                      </div>
                      <div className={`text-sm ${change.change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {change.change > 0 ? '+' : ''}{formatCurrency(change.change)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Top Transfers */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {analysis.market_insights.transfers_in && (
              <div className="bg-white rounded-lg p-5 border border-gray-200">
                <h4 className="font-semibold mb-4 flex items-center">
                  <ArrowUpRight className="w-5 h-5 text-green-600 mr-2" />
                  Most Transferred In
                </h4>
                <div className="space-y-2">
                  {analysis.market_insights.transfers_in.slice(0, 5).map((player, index) => (
                    <div key={index} className="flex justify-between items-center">
                      <span className="font-medium">{player.name}</span>
                      <span className="text-sm text-gray-600">{player.team}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {analysis.market_insights.transfers_out && (
              <div className="bg-white rounded-lg p-5 border border-gray-200">
                <h4 className="font-semibold mb-4 flex items-center">
                  <ArrowDownRight className="w-5 h-5 text-red-600 mr-2" />
                  Most Transferred Out
                </h4>
                <div className="space-y-2">
                  {analysis.market_insights.transfers_out.slice(0, 5).map((player, index) => (
                    <div key={index} className="flex justify-between items-center">
                      <span className="font-medium">{player.name}</span>
                      <span className="text-sm text-gray-600">{player.team}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-8 pt-4 border-t border-gray-200 text-sm text-gray-500 text-center">
        Last updated: {new Date(analysis.analysis_timestamp).toLocaleString()}
      </div>
    </div>
  );
};

export default FantasyFootballAgent;