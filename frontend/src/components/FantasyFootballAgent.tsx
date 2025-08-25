import React, { useState, useEffect } from 'react';
import { 
  Trophy, TrendingUp, Target, 
  Star, RefreshCw, AlertTriangle, Crown, Zap,
  ArrowUpRight, ArrowDownRight,
  Settings, Activity, BarChart3,
  CheckCircle, Clock, PlayCircle,
  Filter, Calendar,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/fantasy';

interface FantasyAnalysis {
  gameweek: number;
  analysis_timestamp: string;
  ai_powered: boolean;
  model_confidence: string; // "high" | "medium" | "low"
  recommendations: {
    transfers?: Array<{
      player_out: string;
      player_in: string;
      predicted_points_gain: number;
      confidence: number;
      risk_level: string; // "low" | "medium" | "high"
      reasoning: string;
      cost_impact: number;
      priority_score: number;
    }>;
    captain?: Array<{
      player: string;
      team: string;
      predicted_points: number;
      confidence: number;
      risk_score: number;
      ownership: number;
      reasoning: string;
      expected_points_range?: {
        floor: number;
        ceiling: number;
      };
      differential_potential?: number;
    }>;
    differentials?: Array<{
      name: string;
      team: string;
      position: string;
      price: number;
      predicted_points: number;
      ownership: number;
      reasoning: string;
    }>;
  };
  insights: {
    market_trends: {
      price_changes?: number;
      [key: string]: any;
    };
    ai_summary: string;
  };
}

interface PlayerPrediction {
  player_id: number;
  name: string;
  team: string;
  position: string;
  current_price: number;
  predicted_points: number;
  predicted_goals: number;
  predicted_assists: number;
  prediction_confidence: number;
  risk_score: number;
  value_score: number;
  next_5_gameweeks: number[];
  current_form: number;
  ownership: number;
}

interface TransferTarget {
  player_id: number;
  name: string;
  team: string;
  position: string;
  price: number;
  predicted_points: number;
  value_score: number;
  risk_score: number;
  confidence: number;
  ownership: number;
  form: number;
  ai_rating: number;
  reasoning: string;
}

interface CaptainAnalysis {
  player: string;
  team: string;
  predicted_points: number;
  confidence: number;
  risk_score: number;
  ownership: number;
  reasoning: string;
  expected_points_range: {
    floor: number;
    ceiling: number;
  };
  differential_potential: number;
}

interface MarketAnalysis {
  price_risers: Array<{
    name: string;
    team: string;
    price_change: number;
    new_price: number;
    predicted_points: number;
    ai_value_score: number;
  }>;
  price_fallers: Array<{
    name: string;
    team: string;
    price_change: number;
    new_price: number;
    predicted_points: number;
    potential_bargain: boolean;
  }>;
  undervalued_gems: Array<{
    name: string;
    team: string;
    current_value: number;
    predicted_value: number;
    upside: number;
    ownership: number;
    confidence: number;
  }>;
  overvalued_assets: Array<{
    name: string;
    team: string;
    current_value: number;
    predicted_value: number;
    downside: number;
    ownership: number;
    risk_warning: boolean;
  }>;
}

interface FixtureAnalysis {
  team: string;
  team_id: number;
  fixtures_analyzed: number;
  average_difficulty: number;
  home_fixtures: number;
  away_fixtures: number;
  ai_recommendation: string;
  reasoning: string;
  fixture_details: Array<{
    gameweek: number;
    opponent: string;
    home_away: string;
    difficulty: number;
  }>;
}

interface ModelStatus {
  status: string;
  models_available: string[];
  performance: Record<string, any>;
  data_initialized: boolean;
  current_gameweek: number;
}

const FantasyFootballAgent: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Model and system state
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  
  // Data state
  const [analysis, setAnalysis] = useState<FantasyAnalysis | null>(null);
  const [predictions, setPredictions] = useState<PlayerPrediction[]>([]);
  const [transferTargets, setTransferTargets] = useState<TransferTarget[]>([]);
  const [captainAnalysis, setCaptainAnalysis] = useState<CaptainAnalysis[]>([]);
  const [marketAnalysis, setMarketAnalysis] = useState<MarketAnalysis | null>(null);
  const [fixtureAnalysis, setFixtureAnalysis] = useState<FixtureAnalysis[]>([]);
  
  // Filter states
  // Filter states
  const [selectedPosition, setSelectedPosition] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<number>(15.0);
  const [minPredictedPoints, setMinPredictedPoints] = useState<number>(50);
  const [riskLevel, setRiskLevel] = useState<string>('medium');
  const [gameweeksAhead, setGameweeksAhead] = useState<number>(5);
  const [currentTeam, setCurrentTeam] = useState<string>('1,373,6,409,444,613,449,427,119,661,430,470,36,668,525');
  const [budget, setBudget] = useState<number>(100.0);

  // Fetch model status
  const fetchModelStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/model-status`);
      if (!response.ok) throw new Error('Failed to fetch model status');
      const data = await response.json();
      setModelStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch model status');
    }
  };

  // Train models
  const trainModels = async (retrain: boolean = false) => {
    setIsTraining(true);
    try {
      const response = await fetch(`${API_BASE}/train-models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ retrain })
      });
      
      if (!response.ok) throw new Error('Failed to start model training');
      
      // Poll for completion
      setTimeout(() => {
        fetchModelStatus();
        setIsTraining(false);
      }, 10000); // Check after 10 seconds
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to train models');
      setIsTraining(false);
    }
  };

  // Fetch comprehensive AI analysis
  const fetchAIAnalysis = async () => {
    setLoading(true);
    setError(null);
    console.log('Fetching AI analysis with params:', {
      analysis_types: 'transfers,captain,differential',
      current_team: currentTeam,
      budget: budget,
      gameweeks_ahead: gameweeksAhead,
      risk_tolerance: riskLevel
    });
    
    try {
      const params = new URLSearchParams({
        analysis_types: 'transfers,captain,differential',
        current_team: currentTeam,
        budget: budget.toString(),
        gameweeks_ahead: gameweeksAhead.toString(),
        risk_tolerance: riskLevel
      });
      
      const url = `${API_BASE}/ai-analyze?${params}`;
      console.log('AI Analysis URL:', url);
      
      const response = await fetch(url);
      console.log('AI Analysis response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('AI Analysis error response:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log('AI Analysis received data:', data);
      
      setAnalysis(data);
    } catch (err) {
      console.error('AI Analysis fetch error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch AI analysis';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Fetch player predictions
  const fetchPredictions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        position: selectedPosition,
        min_minutes: '20',
        limit: '50'
      });
      
      const response = await fetch(`${API_BASE}/player-predictions?${params}`);
      if (!response.ok) throw new Error('Failed to fetch predictions');
      
      const data = await response.json();
      setPredictions(data.predictions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch predictions');
    } finally {
      setLoading(false);
    }
  };

  //   // Fetch player predictions DEBUG
  // const fetchPredictions = async () => {
  //   setLoading(true);
  //   setError(null);
  //   console.log('Fetching predictions with params:', { position: selectedPosition, min_minutes: '50', limit: '50' });
    
  //   try {
  //     const params = new URLSearchParams();
  //     if (selectedPosition) params.append('position', selectedPosition);
  //     params.append('min_minutes', '50');
  //     params.append('limit', '50');
      
  //     const url = `${API_BASE}/player-predictions?${params}`;
  //     console.log('Fetch URL:', url);
      
  //     const response = await fetch(url);
  //     console.log('Response status:', response.status);
      
  //     if (!response.ok) {
  //       const errorText = await response.text();
  //       console.error('Error response:', errorText);
  //       throw new Error(`HTTP ${response.status}: ${errorText}`);
  //     }
      
  //     const data = await response.json();
  //     console.log('Received data:', data);
      
  //     if (data.predictions && Array.isArray(data.predictions)) {
  //       setPredictions(data.predictions);
  //       console.log('Set predictions:', data.predictions.length, 'players');
  //     } else {
  //       console.error('Invalid data structure:', data);
  //       throw new Error('Invalid response format: missing predictions array');
  //     }
  //   } catch (err) {
  //     console.error('Fetch error:', err);
  //     const errorMessage = err instanceof Error ? err.message : 'Failed to fetch predictions';
  //     setError(errorMessage);
  //     setPredictions([]); // Reset predictions on error
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  // Fetch transfer targets
  const fetchTransferTargets = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        position: selectedPosition,
        max_price: maxPrice.toString(),
        min_predicted_points: minPredictedPoints.toString(),
        risk_level: riskLevel,
        limit: '20'
      });
      
      const response = await fetch(`${API_BASE}/transfer-targets?${params}`);
      if (!response.ok) throw new Error('Failed to fetch transfer targets');
      
      const data = await response.json();
      setTransferTargets(data.transfer_targets);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch transfer targets');
    } finally {
      setLoading(false);
    }
  };

  // Fetch captain analysis
  const fetchCaptainAnalysis = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        gameweeks_ahead: gameweeksAhead.toString(),
        include_differentials: 'true',
        min_ownership: '5.0'
      });
      
      const response = await fetch(`${API_BASE}/captain-analysis?${params}`);
      if (!response.ok) throw new Error('Failed to fetch captain analysis');
      
      const data = await response.json();
      setCaptainAnalysis(data.captain_recommendations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch captain analysis');
    } finally {
      setLoading(false);
    }
  };

  // Fetch market analysis
  const fetchMarketAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/market-analysis`);
      if (!response.ok) throw new Error('Failed to fetch market analysis');
      
      const data = await response.json();
      setMarketAnalysis(data.market_analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch market analysis');
    } finally {
      setLoading(false);
    }
  };

  // Fetch fixture analysis
  const fetchFixtureAnalysis = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        gameweeks_ahead: gameweeksAhead.toString()
      });
      
      const response = await fetch(`${API_BASE}/fixture-analysis?${params}`);
      if (!response.ok) throw new Error('Failed to fetch fixture analysis');
      
      const data = await response.json();
      setFixtureAnalysis(data.fixture_analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch fixture analysis');
    } finally {
      setLoading(false);
    }
  };

  // Initialize data
  useEffect(() => {
    fetchModelStatus();
  }, []);

  // Utility functions
  const formatCurrency = (amount: number) => `£${amount.toFixed(1)}m`;

  const formatPercentage = (value: number | string | undefined) => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return `${(num || 0).toFixed(1)}%`;
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

  const getRiskColor = (risk: string | number) => {
    const riskValue = typeof risk === 'string' ? risk.toUpperCase() : 
      risk > 0.7 ? 'HIGH' : risk > 0.4 ? 'MEDIUM' : 'LOW';
    
    switch (riskValue) {
      case 'HIGH': return 'text-red-600';
      case 'MEDIUM': return 'text-yellow-600';
      case 'LOW': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'STRONG_BUY': return 'text-green-700 bg-green-100';
      case 'CONSIDER': return 'text-blue-700 bg-blue-100';
      case 'AVOID': return 'text-red-700 bg-red-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: Trophy },
    { id: 'models', name: 'AI Models', icon: Settings },
    { id: 'predictions', name: 'Predictions', icon: Target },
    { id: 'transfers', name: 'Transfer Targets', icon: RefreshCw },
    { id: 'captain', name: 'Captain Analysis', icon: Crown },
    { id: 'market', name: 'Market Watch', icon: TrendingUp },
    { id: 'fixtures', name: 'Fixtures', icon: Calendar }
  ];

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <AlertTriangle className="w-6 h-6 text-red-500 mr-3" />
          <h3 className="text-lg font-semibold text-red-800">Error</h3>
        </div>
        <p className="text-red-700 mb-4">{error}</p>
        <button
          onClick={() => {setError(null); fetchModelStatus();}}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg shadow-lg p-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Trophy className="w-8 h-8 text-green-600 mr-3" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Fantasy Football Agent</h1>
            <p className="text-sm text-gray-600">
              {modelStatus ? `GW ${modelStatus.current_gameweek} • Status: ${modelStatus.status}` : 'Loading...'}
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8 overflow-x-auto">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
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
          {/* AI Analysis Controls */}
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Zap className="w-5 h-5 text-green-600 mr-2" />
                <h3 className="font-semibold">AI Fantasy Analysis</h3>
              </div>
              <button
                onClick={fetchAIAnalysis}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors flex items-center"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                {loading ? 'Analyzing...' : 'Get AI Analysis'}
              </button>
            </div>
            
            {/* Analysis Parameters */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Current Team (Player IDs)</label>
                <input
                  type="text"
                  value={currentTeam}
                  onChange={(e) => setCurrentTeam(e.target.value)}
                  placeholder="e.g., 1,373,6,409..."
                  className="border border-gray-300 rounded-md px-3 py-2 w-full text-sm"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Budget (£m)</label>
                <input
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  min="0"
                  max="200"
                  step="0.1"
                  className="border border-gray-300 rounded-md px-3 py-2 w-full"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gameweeks Ahead</label>
                <input
                  type="number"
                  value={gameweeksAhead}
                  onChange={(e) => setGameweeksAhead(Number(e.target.value))}
                  min="1"
                  max="10"
                  className="border border-gray-300 rounded-md px-3 py-2 w-full"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Risk Tolerance</label>
                <select
                  value={riskLevel}
                  onChange={(e) => setRiskLevel(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 w-full"
                >
                  <option value="low">Low Risk</option>
                  <option value="medium">Medium Risk</option>
                  <option value="high">High Risk</option>
                </select>
              </div>
            </div>
          </div>

          {analysis ? (
            <>
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
                    <span className="text-sm font-medium text-gray-600">AI Confidence</span>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 mt-1">
                    {analysis.model_confidence}
                  </div>
                </div>
              </div>

              {/* AI Summary */}
              <div className="bg-white rounded-lg p-6 border border-green-100">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Zap className="w-5 h-5 text-green-600 mr-2" />
                  AI Agent Summary
                </h3>
                <div className="prose prose-sm max-w-none">
                  <div className="whitespace-pre-line text-gray-700">
                    {analysis.insights.ai_summary}
                  </div>
                </div>
              </div>

              {/* Top Recommendations */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Top Transfer */}
                {analysis.recommendations.transfers && analysis.recommendations.transfers.length > 0 && (
                  <div className="bg-white rounded-lg p-5 border border-gray-200">
                    <h4 className="font-semibold mb-3 flex items-center">
                      <RefreshCw className="w-5 h-5 text-green-600 mr-2" />
                      Top Transfer
                    </h4>
                    {analysis.recommendations.transfers.slice(0, 1).map((transfer, index) => (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium text-gray-900">{transfer.player_in}</div>
                          <div className="font-bold text-green-600">+{transfer.predicted_points_gain.toFixed(1)} pts</div>
                        </div>
                        <div className="text-sm text-gray-600 mb-2">Out: {transfer.player_out}</div>
                        <div className="text-xs text-gray-500">{transfer.reasoning}</div>
                        <div className="mt-2 flex justify-between text-xs">
                          <span className={`${getRiskColor(transfer.risk_level)}`}>{transfer.risk_level} Risk</span>
                          <span className="text-blue-600">{formatPercentage(transfer.confidence * 100)} Confidence</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Top Captain */}
                {analysis.recommendations.captain && analysis.recommendations.captain.length > 0 && (
                  <div className="bg-white rounded-lg p-5 border border-gray-200">
                    <h4 className="font-semibold mb-3 flex items-center">
                      <Crown className="w-5 h-5 text-yellow-600 mr-2" />
                      Captain Pick
                    </h4>
                    {analysis.recommendations.captain.slice(0, 1).map((captain, index) => (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium text-gray-900">{captain.player}</div>
                          <div className="font-bold text-green-600">{captain.predicted_points.toFixed(1)} pts</div>
                        </div>
                        <div className="text-sm text-gray-600 mb-2">{captain.team}</div>
                        <div className="text-xs text-gray-500">{captain.reasoning}</div>
                        <div className="mt-2 flex justify-between text-xs">
                          <span className="text-purple-600">{formatPercentage(captain.ownership)} Owned</span>
                          <span className="text-blue-600">{formatPercentage(captain.confidence * 100)} Confidence</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Top Differential */}
                {analysis.recommendations.differentials && analysis.recommendations.differentials.length > 0 && (
                  <div className="bg-white rounded-lg p-5 border border-gray-200">
                    <h4 className="font-semibold mb-3 flex items-center">
                      <Star className="w-5 h-5 text-purple-600 mr-2" />
                      Top Differential
                    </h4>
                    {analysis.recommendations.differentials.slice(0, 1).map((diff, index) => (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium text-gray-900">{diff.name}</div>
                          <div className="font-bold text-green-600">{diff.predicted_points.toFixed(1)} pts</div>
                        </div>
                        <div className="text-sm text-gray-600 mb-2">{diff.team} • {formatCurrency(diff.price)}</div>
                        <div className="text-xs text-gray-500">{diff.reasoning}</div>
                        <div className="mt-2 flex justify-between text-xs">
                          <span className="text-purple-600">{formatPercentage(diff.ownership)} Owned</span>
                          <span className={`px-2 py-1 rounded-full ${getPositionColor(diff.position)}`}>
                            {diff.position}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              {/* System Status */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg p-4 border border-green-100">
                  <div className="flex items-center">
                    <CheckCircle className={`w-5 h-5 mr-2 ${modelStatus?.status === 'ready' ? 'text-green-600' : 'text-gray-400'}`} />
                    <span className="text-sm font-medium text-gray-600">Model Status</span>
                  </div>
                  <div className="text-lg font-bold text-gray-900 mt-1">
                    {modelStatus?.status || 'Unknown'}
                  </div>
                </div>
                
                <div className="bg-white rounded-lg p-4 border border-blue-100">
                  <div className="flex items-center">
                    <Activity className="w-5 h-5 text-blue-600 mr-2" />
                    <span className="text-sm font-medium text-gray-600">Models Available</span>
                  </div>
                  <div className="text-lg font-bold text-gray-900 mt-1">
                    {modelStatus?.models_available?.length || 0}
                  </div>
                </div>
                
                <div className="bg-white rounded-lg p-4 border border-purple-100">
                  <div className="flex items-center">
                    <BarChart3 className="w-5 h-5 text-purple-600 mr-2" />
                    <span className="text-sm font-medium text-gray-600">Data Status</span>
                  </div>
                  <div className="text-lg font-bold text-gray-900 mt-1">
                    {modelStatus?.data_initialized ? 'Ready' : 'Not Loaded'}
                  </div>
                </div>
                
                <div className="bg-white rounded-lg p-4 border border-orange-100">
                  <div className="flex items-center">
                    <Calendar className="w-5 h-5 text-orange-600 mr-2" />
                    <span className="text-sm font-medium text-gray-600">Current GW</span>
                  </div>
                  <div className="text-lg font-bold text-gray-900 mt-1">
                    {modelStatus?.current_gameweek || 'N/A'}
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white rounded-lg p-6 border border-gray-200">
                <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <button
                    onClick={fetchAIAnalysis}
                    className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Zap className="w-6 h-6 text-green-600 mb-2" />
                    <span className="text-sm font-medium">AI Analysis</span>
                  </button>
                  
                  <button
                    onClick={() => setActiveTab('predictions')}
                    className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Target className="w-6 h-6 text-green-600 mb-2" />
                    <span className="text-sm font-medium">View Predictions</span>
                  </button>
                  
                  <button
                    onClick={() => setActiveTab('transfers')}
                    className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <RefreshCw className="w-6 h-6 text-blue-600 mb-2" />
                    <span className="text-sm font-medium">Transfer Targets</span>
                  </button>
                  
                  <button
                    onClick={() => setActiveTab('market')}
                    className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <TrendingUp className="w-6 h-6 text-purple-600 mb-2" />
                    <span className="text-sm font-medium">Market Watch</span>
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === 'models' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Settings className="w-5 h-5 text-gray-600 mr-2" />
              AI Model Management
            </h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h4 className="font-medium">Model Training Status</h4>
                  <p className="text-sm text-gray-600">
                    {isTraining ? 'Training in progress...' : 'Models ready for training'}
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={() => trainModels(false)}
                    disabled={isTraining}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors flex items-center"
                  >
                    {isTraining ? <Clock className="w-4 h-4 mr-2" /> : <PlayCircle className="w-4 h-4 mr-2" />}
                    {isTraining ? 'Training...' : 'Train Models'}
                  </button>
                  
                  <button
                    onClick={() => trainModels(true)}
                    disabled={isTraining}
                    className="bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors flex items-center"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Retrain All
                  </button>
                </div>
              </div>

              {modelStatus?.models_available && (
                <div className="space-y-2">
                  <h4 className="font-medium">Available Models:</h4>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {modelStatus.models_available.map((model, index) => (
                      <div key={index} className="px-3 py-2 bg-green-100 text-green-800 rounded-md text-sm">
                        {model}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {modelStatus?.performance && (
                <div>
                  <h4 className="font-medium mb-2">Model Performance:</h4>
                  <div className="bg-gray-50 p-3 rounded-lg text-sm">
                    <pre className="whitespace-pre-wrap">
                      {JSON.stringify(modelStatus.performance, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'predictions' && (
        <div className="space-y-6">
          {/* Filters */}
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center mb-3">
              <Filter className="w-5 h-5 text-gray-600 mr-2" />
              <h3 className="font-semibold">Filters</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <select
                value={selectedPosition}
                onChange={(e) => setSelectedPosition(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="">All Positions</option>
                <option value="GKP">Goalkeeper</option>
                <option value="DEF">Defender</option>
                <option value="MID">Midfielder</option>
                <option value="FWD">Forward</option>
              </select>
              
              <button
                onClick={fetchPredictions}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors"
              >
                {loading ? 'Loading...' : 'Get Predictions'}
              </button>
            </div>
          </div>

          {/* Predictions Table */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Player Predictions ({predictions.length})</h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Player</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Team</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Position</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pred. Points</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {predictions.map((player, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="font-medium text-gray-900">{player.name}</div>
                        <div className="text-sm text-gray-500">{formatPercentage(player.ownership)} owned</div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">{player.team}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPositionColor(player.position)}`}>
                          {player.position}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">{formatCurrency(player.current_price)}</td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">{player.predicted_points}</div>
                        <div className="text-xs text-gray-500">G: {player.predicted_goals} A: {player.predicted_assists}</div>
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-green-600">{player.value_score.toFixed(1)}</td>
                      <td className="px-6 py-4">
                        <span className={`text-sm font-medium ${getRiskColor(player.risk_score)}`}>
                          {player.risk_score.toFixed(2)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {formatPercentage(player.prediction_confidence * 100)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'transfers' && (
        <div className="space-y-6">
          {/* Filters */}
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center mb-3">
              <Filter className="w-5 h-5 text-gray-600 mr-2" />
              <h3 className="font-semibold">Transfer Target Filters</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <select
                value={selectedPosition}
                onChange={(e) => setSelectedPosition(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="">All Positions</option>
                <option value="GKP">Goalkeeper</option>
                <option value="DEF">Defender</option>
                <option value="MID">Midfielder</option>
                <option value="FWD">Forward</option>
              </select>
              
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(Number(e.target.value))}
                placeholder="Max Price"
                step="0.5"
                className="border border-gray-300 rounded-md px-3 py-2"
              />
              
              <input
                type="number"
                value={minPredictedPoints}
                onChange={(e) => setMinPredictedPoints(Number(e.target.value))}
                placeholder="Min Predicted Points"
                className="border border-gray-300 rounded-md px-3 py-2"
              />
              
              <select
                value={riskLevel}
                onChange={(e) => setRiskLevel(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="low">Low Risk</option>
                <option value="medium">Medium Risk</option>
                <option value="high">High Risk</option>
              </select>
              
              <button
                onClick={fetchTransferTargets}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors"
              >
                {loading ? 'Loading...' : 'Find Targets'}
              </button>
            </div>
          </div>

          {/* Transfer Targets */}
          <div className="space-y-4">
            {transferTargets.map((target, index) => (
              <div key={index} className="bg-white rounded-lg p-5 border border-gray-200 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <h4 className="font-semibold text-lg text-gray-900 mr-3">{target.name}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPositionColor(target.position)}`}>
                        {target.position}
                      </span>
                      <span className="ml-2 text-sm text-gray-600">({target.team})</span>
                    </div>
                    <p className="text-gray-600 mb-2">{target.reasoning}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-green-600">
                      AI Rating: {target.ai_rating}
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatCurrency(target.price)}
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Predicted Points:</span>
                    <div className="font-semibold text-green-600">{target.predicted_points.toFixed(1)}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Value Score:</span>
                    <div className="font-semibold text-purple-600">{target.value_score.toFixed(1)}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Risk Score:</span>
                    <div className={`font-semibold ${getRiskColor(target.risk_score)}`}>
                      {target.risk_score.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500">Confidence:</span>
                    <div className="font-semibold text-blue-600">
                      {formatPercentage(target.confidence * 100)}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500">Ownership:</span>
                    <div className="font-semibold">{formatPercentage(target.ownership)}</div>
                  </div>
                </div>
              </div>
            ))}
            
            {transferTargets.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No transfer targets found. Adjust your filters or click "Find Targets" to search.
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'captain' && (
        <div className="space-y-6">
          {/* Captain Analysis Controls */}
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center mb-3">
              <Crown className="w-5 h-5 text-yellow-600 mr-2" />
              <h3 className="font-semibold">Captain Analysis</h3>
            </div>
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <span className="text-sm text-gray-600 mr-2">Gameweeks ahead:</span>
                <input
                  type="number"
                  value={gameweeksAhead}
                  onChange={(e) => setGameweeksAhead(Number(e.target.value))}
                  min="1"
                  max="10"
                  className="border border-gray-300 rounded-md px-3 py-2 w-20"
                />
              </label>
              
              <button
                onClick={fetchCaptainAnalysis}
                disabled={loading}
                className="bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors"
              >
                {loading ? 'Analyzing...' : 'Analyze Captains'}
              </button>
            </div>
          </div>

          {/* Captain Recommendations */}
          <div className="space-y-4">
            {captainAnalysis.map((captain, index) => (
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
                    <p className="text-gray-600">{captain.reasoning}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-green-600 font-medium">Predicted</div>
                    <div className="text-lg font-bold text-green-800">
                      {captain.predicted_points.toFixed(1)} pts
                    </div>
                  </div>
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="text-blue-600 font-medium">Confidence</div>
                    <div className="text-lg font-bold text-blue-800">
                      {formatPercentage(captain.confidence * 100)}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded-lg">
                    <div className="text-red-600 font-medium">Risk Score</div>
                    <div className="text-lg font-bold text-red-800">
                      {captain.risk_score.toFixed(3)}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded-lg">
                    <div className="text-purple-600 font-medium">Ownership</div>
                    <div className="text-lg font-bold text-purple-800">
                      {formatPercentage(captain.ownership)}
                    </div>
                  </div>
                </div>
                
                {captain.expected_points_range && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">Expected Range:</span>
                    <span className="text-sm font-medium">
                      {captain.expected_points_range.floor} - {captain.expected_points_range.ceiling} points
                    </span>
                  </div>
                )}
              </div>
            ))}
            
            {captainAnalysis.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No captain analysis available. Click "Analyze Captains" to get recommendations.
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'market' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">Market Analysis</h3>
            <button
              onClick={fetchMarketAnalysis}
              disabled={loading}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors"
            >
              {loading ? 'Loading...' : 'Refresh Market'}
            </button>
          </div>
          
          {marketAnalysis && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Price Risers */}
              <div className="bg-white rounded-lg p-5 border border-gray-200">
                <h4 className="font-semibold mb-4 flex items-center">
                  <ArrowUpRight className="w-5 h-5 text-green-600 mr-2" />
                  Price Risers ({marketAnalysis.price_risers?.length || 0})
                </h4>
                <div className="space-y-3">
                  {marketAnalysis.price_risers?.map((player, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <div>
                        <div className="font-medium">{player.name}</div>
                        <div className="text-sm text-gray-600">{player.team}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-green-600">
                          +{formatCurrency(Math.abs(player.price_change))}
                        </div>
                        <div className="text-sm text-gray-600">
                          {formatCurrency(player.new_price)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Price Fallers */}
              <div className="bg-white rounded-lg p-5 border border-gray-200">
                <h4 className="font-semibold mb-4 flex items-center">
                  <ArrowDownRight className="w-5 h-5 text-red-600 mr-2" />
                  Price Fallers ({marketAnalysis.price_fallers?.length || 0})
                </h4>
                <div className="space-y-3">
                  {marketAnalysis.price_fallers?.map((player, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                      <div>
                        <div className="font-medium">{player.name}</div>
                        <div className="text-sm text-gray-600">{player.team}</div>
                        {player.potential_bargain && (
                          <div className="text-xs text-green-600 font-medium">Potential Bargain</div>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-red-600">
                          {formatCurrency(player.price_change)}
                        </div>
                        <div className="text-sm text-gray-600">
                          {formatCurrency(player.new_price)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Undervalued Gems */}
              <div className="bg-white rounded-lg p-5 border border-gray-200">
                <h4 className="font-semibold mb-4 flex items-center">
                  <Star className="w-5 h-5 text-green-600 mr-2" />
                  Undervalued Gems ({marketAnalysis.undervalued_gems?.length || 0})
                </h4>
                <div className="space-y-3">
                  {marketAnalysis.undervalued_gems?.map((player, index) => (
                    <div key={index} className="p-3 bg-green-50 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-medium">{player.name}</div>
                          <div className="text-sm text-gray-600">{player.team}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold text-green-600">
                            +{player.upside.toFixed(1)}% upside
                          </div>
                          <div className="text-sm text-gray-600">
                            {formatPercentage(player.ownership)} owned
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500">
                        Current: {player.current_value.toFixed(2)} → Predicted: {player.predicted_value.toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Overvalued Assets */}
              <div className="bg-white rounded-lg p-5 border border-gray-200">
                <h4 className="font-semibold mb-4 flex items-center">
                  <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
                  Overvalued Assets ({marketAnalysis.overvalued_assets?.length || 0})
                </h4>
                <div className="space-y-3">
                  {marketAnalysis.overvalued_assets?.map((player, index) => (
                    <div key={index} className="p-3 bg-red-50 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-medium">{player.name}</div>
                          <div className="text-sm text-gray-600">{player.team}</div>
                          {player.risk_warning && (
                            <div className="text-xs text-red-600 font-medium">High Risk</div>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="font-semibold text-red-600">
                            -{player.downside.toFixed(1)}% downside
                          </div>
                          <div className="text-sm text-gray-600">
                            {formatPercentage(player.ownership)} owned
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500">
                        Current: {player.current_value.toFixed(2)} → Predicted: {player.predicted_value.toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {!marketAnalysis && (
            <div className="text-center py-8 text-gray-500">
              Click "Refresh Market" to get the latest market analysis.
            </div>
          )}
        </div>
      )}

      {activeTab === 'fixtures' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Calendar className="w-5 h-5 text-blue-600 mr-2" />
                <h3 className="font-semibold">Fixture Analysis</h3>
              </div>
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <span className="text-sm text-gray-600 mr-2">Gameweeks ahead:</span>
                  <input
                    type="number"
                    value={gameweeksAhead}
                    onChange={(e) => setGameweeksAhead(Number(e.target.value))}
                    min="1"
                    max="10"
                    className="border border-gray-300 rounded-md px-3 py-2 w-20"
                  />
                </label>
                
                <button
                  onClick={fetchFixtureAnalysis}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors"
                >
                  {loading ? 'Analyzing...' : 'Analyze Fixtures'}
                </button>
              </div>
            </div>
          </div>

          {/* Fixture Analysis Results */}
          <div className="space-y-4">
            {fixtureAnalysis.map((team, index) => (
              <div key={index} className="bg-white rounded-lg p-5 border border-gray-200">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <h4 className="font-semibold text-lg text-gray-900 mr-3">
                        {team.team}
                      </h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRecommendationColor(team.ai_recommendation)}`}>
                        {team.ai_recommendation.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-3">{team.reasoning}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900">
                      Difficulty: {team.average_difficulty.toFixed(1)}
                    </div>
                    <div className="text-sm text-gray-500">
                      {team.fixtures_analyzed} fixtures
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="text-blue-600 font-medium text-sm">Home</div>
                    <div className="text-lg font-bold text-blue-800">
                      {team.home_fixtures}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-lg">
                    <div className="text-orange-600 font-medium text-sm">Away</div>
                    <div className="text-lg font-bold text-orange-800">
                      {team.away_fixtures}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-gray-600 font-medium text-sm">Avg Difficulty</div>
                    <div className="text-lg font-bold text-gray-800">
                      {team.average_difficulty.toFixed(1)}/5
                    </div>
                  </div>
                </div>
                
                {/* Fixture Details */}
                <div className="space-y-2">
                  <h5 className="font-medium text-sm text-gray-700">Upcoming Fixtures:</h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {team.fixture_details.map((fixture, fIndex) => (
                      <div key={fIndex} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                        <span className="font-medium">GW{fixture.gameweek}</span>
                        <span className={fixture.home_away === 'H' ? 'text-blue-600' : 'text-orange-600'}>
                          {fixture.home_away === 'H' ? 'vs' : '@'} {fixture.opponent}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          fixture.difficulty <= 2 ? 'bg-green-100 text-green-800' :
                          fixture.difficulty >= 4 ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {fixture.difficulty}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
            
            {fixtureAnalysis.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No fixture analysis available. Click "Analyze Fixtures" to get team fixture difficulty.
              </div>
            )}
          </div>
        </div>
      )}

      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center">
            <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-3" />
            <span>Loading data...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default FantasyFootballAgent;
                