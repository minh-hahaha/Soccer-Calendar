from datetime import datetime
from typing import Optional, List
import os

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..fantasy.fantasy_agent import FantasyAdviceType, FantasyFootballAgent

router = APIRouter()

fantasy_agent = FantasyFootballAgent()

# @router.get("/analyze")
# def analyze_fantasy_strategy(
#     analysis_types: str = Query("transfers,captain,differential", description="Comma-separated analysis types"),
#     budget: float = Query(100.0, description="Available budget in millions"),
#     gameweeks_ahead: int = Query(5, description="Number of gameweeks to analyze ahead"),
#     current_team: Optional[str] = Query(None, description="Comma-separated player IDs (current team)")
# ):
#     """
#     Get comprehensive Fantasy Football analysis and recommendations
#     """
#     # Parse analysis types
#     requested_types = []
#     for analysis_type in analysis_types.split(","):
#         analysis_type = analysis_type.strip()
#         if analysis_type in [e.value for e in FantasyAdviceType]:
#             requested_types.append(FantasyAdviceType(analysis_type))
    
#     if not requested_types:
#         requested_types = [FantasyAdviceType.TRANSFER, FantasyAdviceType.CAPTAIN]
    
#     # Parse current team if provided
#     current_team_ids = None
#     if current_team:
#         try:
#             current_team_ids = [int(x.strip()) for x in current_team.split(",")]
#         except:
#             current_team_ids = None
    
#     return fantasy_agent.analyze_fantasy_strategy(
#         analysis_types=requested_types,
#         budget=budget,
#         current_team=current_team_ids,
#         gameweeks_ahead=gameweeks_ahead
#     )

# @router.get("/captain-analysis")
# def get_captain_analysis(
#     gameweeks_ahead: int = Query(1, description="Gameweeks to analyze")
# ):
#     """Get detailed captain analysis"""
#     if not fantasy_agent.bootstrap_data:
#         fantasy_agent.initialize_data()
    
#     return {
#         "captain_options": fantasy_agent._analyze_captain_options(gameweeks_ahead),
#         "gameweek": fantasy_agent.current_gameweek,
#         "analysis_type": "captain_focus"
#     }

# @router.get("/transfer-targets")
# def get_transfer_targets(
#     budget: float = Query(100.0), 
#     position: Optional[str] = Query(None)
# ):
#     """Get transfer targets by position"""
#     if not fantasy_agent.bootstrap_data:
#         fantasy_agent.initialize_data()
    
#     transfers = fantasy_agent._analyze_transfers(budget)
    
#     if position:
#         # Filter by position if specified
#         position_map = {"gkp": "Goalkeeper", "def": "Defender", "mid": "Midfielder", "fwd": "Forward"}
#         target_position = position_map.get(position.lower())
#         if target_position:
#             # Would need to filter transfers by position
#             pass
    
#     return {
#         "transfer_targets": transfers,
#         "budget": budget,
#         "gameweek": fantasy_agent.current_gameweek
#     }

# @router.get("/market-watch")
# def get_market_insights():
#     """Get current FPL market insights"""
#     if not fantasy_agent.bootstrap_data:
#         fantasy_agent.initialize_data()
    
#     return {
#         "market_insights": fantasy_agent._get_market_insights(),
#         "gameweek": fantasy_agent.current_gameweek,
#         "last_updated": datetime.utcnow().isoformat()
#     }

# @router.get("/differentials")
# def get_differential_picks(
#     max_ownership: float = Query(5.0, description="Maximum ownership percentage")
# ):
#     """Get differential pick recommendations"""
#     if not fantasy_agent.bootstrap_data:
#         fantasy_agent.initialize_data()
    
#     return {
#         "differentials": fantasy_agent._analyze_differential_picks(),
#         "max_ownership": max_ownership,
#         "gameweek": fantasy_agent.current_gameweek
#     }

# @router.get("/health")
# def fantasy_agent_health():
#     """Health check for fantasy agent"""
#     return {
#         "status": "ok",
#         "agent_version": "1.0.0",
#         "data_initialized": fantasy_agent.bootstrap_data is not None,
#         "current_gameweek": fantasy_agent.current_gameweek,
#         "capabilities": [e.value for e in FantasyAdviceType]
#     }

# Initialize AI agent with database connection
DB_CONNECTION = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/football")
ai_agent = FantasyFootballAgent(DB_CONNECTION)

# Pydantic models for request/response
class TrainModelRequest(BaseModel):
    retrain: bool = False
    seasons_to_include: List[str] = ["2016-17", "2017-18", "2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

class PlayerPredictionResponse(BaseModel):
    player_id: int
    name: str
    predicted_points: float
    predicted_goals: float
    predicted_assists: float
    prediction_confidence: float
    risk_score: float
    value_score: float


class TransferRecommendationResponse(BaseModel):
    player_out: str
    player_in: str
    predicted_points_gain: float
    confidence: float
    risk_level: str
    reasoning: str
    cost_impact: float
    priority_score: float

@router.post("/train-models")
async def train_ai_models(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks
):
    """Train or retrain the AI models (runs in background)"""
    def train_models():
        try:
            ai_agent.initialize_data()
            if request.retrain or not ai_agent.models:
                ai_agent.train_prediction_models()
                return {"status": "success", "message": "Models trained successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Training failed: {str(e)}"}
    
    # Run training in background
    background_tasks.add_task(train_models)
    
    return {
        "status": "started",
        "message": "Model training started in background",
        "estimated_time": "5-10 minutes"
    }

@router.get("/model-status")
async def get_model_status():
    """Get current model status and performance metrics"""
    if not ai_agent.models:
        # Try to load existing models
        if not ai_agent.load_models():
            return {
                "status": "not_trained",
                "message": "Models need to be trained first",
                "models_available": [],
                "last_trained": None
            }
    
    performance_report = ai_agent.get_model_performance_report()
    
    return {
        "status": "ready",
        "models_available": list(ai_agent.models.keys()),
        "performance": performance_report,
        "data_initialized": ai_agent.bootstrap_data is not None,
        "current_gameweek": ai_agent.current_gameweek
    }


# different types of analysis 
@router.get("/ai-analyze")
async def ai_analyze_fantasy_strategy(
    analysis_types: str = Query("transfers,captain,differential", description="Comma-separated analysis types"),
    current_team: str = Query(..., description="Comma-separated current player IDs"),
    budget: float = Query(2.0, description="Available budget for transfers"),
    gameweeks_ahead: int = Query(5, description="Number of gameweeks to analyze ahead"),
    risk_tolerance: str = Query("medium", description="Risk tolerance: low, medium, high")
):
    """
    Get AI-powered Fantasy Football analysis and recommendations
    """
    if not ai_agent.models:
        # Try to load models
        if not ai_agent.load_models():
            raise HTTPException(status_code=503, detail="AI models not available. Train models first.")
    
    if not ai_agent.bootstrap_data:
        if not ai_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize current season data")
    
    # Parse current team
    try:
        current_team_ids = [int(x.strip()) for x in current_team.split(",")]
    except:
        raise HTTPException(status_code=400, detail="Invalid current team format")
    
    # Parse analysis types
    requested_types = [t.strip() for t in analysis_types.split(",")]
    
    analysis_results = {
        "gameweek": ai_agent.current_gameweek,
        "analysis_timestamp": datetime.now().isoformat(),
        "ai_powered": True,
        "model_confidence": "high" if min(ai_agent.model_performance.values(), key=lambda x: x['r2'])['r2'] > 0.3 else "medium",
        "recommendations": {},
        "insights": {
            "market_trends": ai_agent._get_market_insights() if hasattr(ai_agent, '_get_market_insights') else {},
            "ai_summary": ""
        }
    }
    
    # AI Transfer Analysis
    if "transfers" in requested_types:
        transfer_recs = ai_agent.get_ai_transfer_recommendations(current_team_ids, budget)
        analysis_results["recommendations"]["transfers"] = [
            {
                "player_out": t.player_out,
                "player_in": t.player_in,
                "predicted_points_gain": round(t.predicted_points_gain, 1),
                "confidence": round(t.confidence, 3),
                "risk_level": t.risk_level,
                "reasoning": t.reasoning,
                "cost_impact": t.cost_impact,
                "priority_score": round(t.predicted_points_gain * t.confidence, 2)
            } for t in transfer_recs
        ]
    
    # AI Captain Analysis
    if "captain" in requested_types:
        captain_recs = ai_agent.get_ai_captain_recommendations(gameweeks_ahead)
        analysis_results["recommendations"]["captain"] = captain_recs
    
    # AI Differential Picks
    if "differential" in requested_types:
        analysis_results["recommendations"]["differentials"] = ai_agent.get_ai_differential_picks(risk_tolerance)
    
    # Generate AI summary
    analysis_results["insights"]["ai_summary"] = generate_ai_summary(analysis_results, risk_tolerance)
    
    return analysis_results

@router.get("/player-predictions")
async def get_player_predictions(
    player_ids: Optional[str] = Query(None, description="Comma-separated player IDs, if None returns top predictions"),
    position: Optional[str] = Query(None, description="Filter by position: GKP, DEF, MID, FWD"),
    min_minutes: int = Query(200, description="Minimum minutes played"),
    limit: int = Query(20, description="Maximum number of players to return")
):
    """Get AI predictions for specific players or top performers"""
    
    if not ai_agent.models:
        if not ai_agent.load_models():
            raise HTTPException(status_code=503, detail="AI models not available")
    
    if not ai_agent.bootstrap_data:
        if not ai_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize data")
    
    players = ai_agent.bootstrap_data['elements']
    
    # Filter players
    if player_ids:
        target_ids = [int(x.strip()) for x in player_ids.split(",")]
        players = [p for p in players if p['id'] in target_ids]
    
    if position:
        position_map = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}
        if position in position_map:
            players = [p for p in players if p['element_type'] == position_map[position]]
    
    # Filter by minimum minutes
    players = [p for p in players if p.get('minutes', 0) >= min_minutes]
    
    predictions = []
    for player in players[:limit]:
        try:
            pred = ai_agent.predict_player_performance(player)
            predictions.append({
                "player_id": pred.player_id,
                "name": pred.name,
                "team": ai_agent._get_team_name(player['team']),
                "position": ai_agent._get_position_name(player['element_type']),
                "current_price": player['now_cost'] / 10,
                "predicted_points": round(pred.predicted_points, 1),
                "predicted_goals": round(pred.predicted_goals, 1),
                "predicted_assists": round(pred.predicted_assists, 1),
                "prediction_confidence": round(pred.prediction_confidence, 3),
                "risk_score": round(pred.risk_score, 3),
                "value_score": round(pred.value_score, 2),
                "next_5_gameweeks": [round(x, 1) for x in pred.next_5_gameweeks],
                "current_form": player.get('form', 0),
                "ownership": player.get('selected_by_percent', 0)
            })
        except Exception as e:
            continue  # Skip players with prediction errors
    
    # Sort by predicted points
    predictions.sort(key=lambda x: x['predicted_points'], reverse=True)
    
    return {
        "predictions": predictions,
        "total_players": len(predictions),
        "filter_applied": {
            "position": position,
            "min_minutes": min_minutes,
            "specific_players": player_ids is not None
        },
        "model_info": {
            "confidence": "high" if min(ai_agent.model_performance.values(), key=lambda x: x['r2'])['r2'] > 0.3 else "medium",
            "last_trained": datetime.now().isoformat()  # Would store actual training time
        }
    }

@router.get("/transfer-targets")
async def get_ai_transfer_targets(
    position: Optional[str] = Query(None, description="Position filter: GKP, DEF, MID, FWD"),
    max_price: float = Query(15.0, description="Maximum price"),
    min_predicted_points: float = Query(50.0, description="Minimum predicted points"),
    risk_level: str = Query("medium", description="Max risk level: low, medium, high"),
    limit: int = Query(10, description="Number of targets to return")
):
    """Get AI-recommended transfer targets"""
    
    if not ai_agent.models:
        if not ai_agent.load_models():
            raise HTTPException(status_code=503, detail="AI models not available")
    
    if not ai_agent.bootstrap_data:
        if not ai_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize data")
    
    players = ai_agent.bootstrap_data['elements']
    
    # Apply filters
    if position:
        position_map = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}
        if position in position_map:
            players = [p for p in players if p['element_type'] == position_map[position]]
    
    # Price filter
    players = [p for p in players if p['now_cost'] / 10 <= max_price]
    
    # Only players with reasonable minutes
    players = [p for p in players if p.get('minutes', 0) > 100]
    
    transfer_targets = []
    risk_thresholds = {"low": 0.3, "medium": 0.6, "high": 1.0}
    max_risk = risk_thresholds.get(risk_level, 0.6)
    
    for player in players:
        try:
            pred = ai_agent.predict_player_performance(player)
            
            if pred.predicted_points >= min_predicted_points and pred.risk_score <= max_risk:
                transfer_targets.append({
                    "player_id": pred.player_id,
                    "name": pred.name,
                    "team": ai_agent._get_team_name(player['team']),
                    "position": ai_agent._get_position_name(player['element_type']),
                    "price": player['now_cost'] / 10,
                    "predicted_points": round(pred.predicted_points, 1),
                    "value_score": round(pred.value_score, 2),
                    "risk_score": round(pred.risk_score, 3),
                    "confidence": round(pred.prediction_confidence, 3),
                    "ownership": float(player.get('selected_by_percent', 0)),
                    "form": float(player.get('form', 0)),
                    "ai_rating": round(pred.predicted_points * pred.prediction_confidence / pred.risk_score, 1),
                    "reasoning": generate_transfer_reasoning(pred, player)
                })
        except Exception as e:
            continue
    
    # Sort by AI rating (predicted points * confidence / risk)
    transfer_targets.sort(key=lambda x: x['ai_rating'], reverse=True)
    
    return {
        "transfer_targets": transfer_targets[:limit],
        "filters_applied": {
            "position": position,
            "max_price": max_price,
            "min_predicted_points": min_predicted_points,
            "risk_level": risk_level
        },
        "total_found": len(transfer_targets),
        "recommendation": "Focus on high AI rating players for best risk-adjusted returns"
    }

@router.get("/captain-analysis")
async def get_ai_captain_analysis(
    gameweeks_ahead: int = Query(1, description="Gameweeks to analyze"),
    include_differentials: bool = Query(False, description="Include differential captain options"),
    min_ownership: float = Query(5.0, description="Minimum ownership percentage")
):
    """Get detailed AI captain analysis"""
    
    if not ai_agent.models:
        if not ai_agent.load_models():
            raise HTTPException(status_code=503, detail="AI models not available")
    
    if not ai_agent.bootstrap_data:
        if not ai_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize data")
    
    captain_analysis = ai_agent.get_ai_captain_recommendations(gameweeks_ahead)
    
    # Filter by ownership if needed
    if not include_differentials:
        captain_analysis = [c for c in captain_analysis if c['ownership'] >= min_ownership]
    
    # Add additional analysis
    for captain in captain_analysis:
        captain['expected_points_range'] = {
            'floor': round(captain['predicted_points'] * 0.3, 1),
            'ceiling': round(captain['predicted_points'] * 1.8, 1)
        }
        captain['differential_potential'] = round((50 - captain['ownership']) / 50, 2)
        
    return {
        "captain_recommendations": captain_analysis,
        "gameweeks_analyzed": gameweeks_ahead,
        "analysis_type": "ai_powered",
        "metadata": {
            "include_differentials": include_differentials,
            "min_ownership": min_ownership,
            "total_options": len(captain_analysis)
        },
        "strategy_note": "AI recommendations based on predicted points, fixture difficulty, and risk assessment"
    }

@router.get("/market-analysis")
async def get_ai_market_analysis():
    """Get AI-powered market analysis and trends"""
    
    if not ai_agent.bootstrap_data:
        if not ai_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize data")
    
    players = ai_agent.bootstrap_data['elements']
    
    # Market trends analysis
    price_risers = []
    price_fallers = []
    undervalued_picks = []
    overvalued_picks = []
    
    for player in players:
        if player.get('minutes', 0) < 100:
            continue
            
        try:
            if ai_agent.models:
                pred = ai_agent.predict_player_performance(player)
                
                # Price change analysis
                if player.get('cost_change_event', 0) > 0:
                    price_risers.append({
                        "name": f"{player['first_name']} {player['second_name']}",
                        "team": ai_agent._get_team_name(player['team']),
                        "price_change": player['cost_change_event'] / 10,
                        "new_price": player['now_cost'] / 10,
                        "predicted_points": round(pred.predicted_points, 1),
                        "ai_value_score": round(pred.value_score, 2)
                    })
                elif player.get('cost_change_event', 0) < 0:
                    price_fallers.append({
                        "name": f"{player['first_name']} {player['second_name']}",
                        "team": ai_agent._get_team_name(player['team']),
                        "price_change": player['cost_change_event'] / 10,
                        "new_price": player['now_cost'] / 10,
                        "predicted_points": round(pred.predicted_points, 1),
                        "potential_bargain": pred.value_score > 2.0
                    })
                
                # Value analysis
                current_value = player['total_points'] / (player['now_cost'] / 10)
                predicted_value = pred.predicted_points / (player['now_cost'] / 10)
                
                if predicted_value > current_value * 1.2 and float(player.get('selected_by_percent', 0)) < 10:
                    undervalued_picks.append({
                        "name": f"{player['first_name']} {player['second_name']}",
                        "team": ai_agent._get_team_name(player['team']),
                        "current_value": round(current_value, 2),
                        "predicted_value": round(predicted_value, 2),
                        "upside": round((predicted_value - current_value) / current_value * 100, 1),
                        "ownership": float(player.get('selected_by_percent', 0)),
                        "confidence": round(pred.prediction_confidence, 3)
                    })
                
                elif predicted_value < current_value * 0.8 and float(player.get('selected_by_percent', 0)) > 15:
                    overvalued_picks.append({
                        "name": f"{player['first_name']} {player['second_name']}",
                        "team": ai_agent._get_team_name(player['team']),
                        "current_value": round(current_value, 2),
                        "predicted_value": round(predicted_value, 2),
                        "downside": round((current_value - predicted_value) / current_value * 100, 1),
                        "ownership": float(player.get('selected_by_percent', 0)),
                        "risk_warning": pred.risk_score > 0.5
                    })
        except:
            continue
    
    # Sort results
    price_risers.sort(key=lambda x: abs(x['price_change']), reverse=True)
    price_fallers.sort(key=lambda x: abs(x['price_change']), reverse=True)
    undervalued_picks.sort(key=lambda x: x['upside'], reverse=True)
    overvalued_picks.sort(key=lambda x: x['downside'], reverse=True)
    
    return {
        "market_analysis": {
            "price_risers": price_risers[:10],
            "price_fallers": price_fallers[:10],
            "undervalued_gems": undervalued_picks[:10],
            "overvalued_assets": overvalued_picks[:10]
        },
        "ai_insights": {
            "market_sentiment": "bullish" if len(price_risers) > len(price_fallers) else "bearish",
            "value_opportunities": len(undervalued_picks),
            "risk_warnings": len(overvalued_picks)
        },
        "analysis_timestamp": datetime.now().isoformat(),
        "gameweek": ai_agent.current_gameweek
    }

@router.get("/fixture-analysis")
async def get_ai_fixture_analysis(
    gameweeks_ahead: int = Query(5, description="Number of gameweeks to analyze"),
    team_ids: Optional[str] = Query(None, description="Specific team IDs to analyze")
):
    """Get AI-powered fixture difficulty and planning analysis"""
    
    if not ai_agent.bootstrap_data or not ai_agent.fixtures_data:
        if not ai_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize data")
    
    teams = ai_agent.bootstrap_data['teams']
    
    if team_ids:
        target_team_ids = [int(x.strip()) for x in team_ids.split(",")]
        teams = [t for t in teams if t['id'] in target_team_ids]
    
    fixture_analysis = []
    
    for team in teams:
        team_fixtures = ai_agent._get_team_fixtures(team['id'], gameweeks_ahead)
        
        if team_fixtures:
            difficulties = []
            home_fixtures = 0
            
            for fixture in team_fixtures:
                difficulty = fixture.get('team_h_difficulty' if fixture['team_h'] == team['id'] else 'team_a_difficulty', 3)
                difficulties.append(difficulty)
                
                if fixture['team_h'] == team['id']:
                    home_fixtures += 1
            
            avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 3
            
            # AI recommendation based on fixture difficulty
            if avg_difficulty <= 2.5:
                recommendation = "STRONG_BUY"
                reasoning = "Excellent fixture run ahead"
            elif avg_difficulty <= 3.2:
                recommendation = "CONSIDER"
                reasoning = "Decent fixture difficulty"
            else:
                recommendation = "AVOID"
                reasoning = "Difficult fixtures ahead"
            
            fixture_analysis.append({
                "team": team['name'],
                "team_id": team['id'],
                "fixtures_analyzed": len(team_fixtures),
                "average_difficulty": round(avg_difficulty, 2),
                "home_fixtures": home_fixtures,
                "away_fixtures": len(team_fixtures) - home_fixtures,
                "ai_recommendation": recommendation,
                "reasoning": reasoning,
                "fixture_details": [
                    {
                        "gameweek": f['event'],
                        "opponent": ai_agent._get_team_name(f['team_a'] if f['team_h'] == team['id'] else f['team_h']),
                        "home_away": "H" if f['team_h'] == team['id'] else "A",
                        "difficulty": f.get('team_h_difficulty' if f['team_h'] == team['id'] else 'team_a_difficulty', 3)
                    } for f in team_fixtures
                ]
            })
    
    # Sort by fixture difficulty (best first)
    fixture_analysis.sort(key=lambda x: x['average_difficulty'])
    
    return {
        "fixture_analysis": fixture_analysis,
        "gameweeks_analyzed": gameweeks_ahead,
        "best_fixtures": fixture_analysis[:5],
        "worst_fixtures": fixture_analysis[-5:],
        "analysis_summary": {
            "teams_analyzed": len(fixture_analysis),
            "average_difficulty": round(sum(t['average_difficulty'] for t in fixture_analysis) / len(fixture_analysis), 2) if fixture_analysis else 0
        }
    }

@router.get("/health")
async def ai_agent_health():
    """Health check for AI fantasy agent"""
    model_status = "ready" if ai_agent.models else "not_trained"
    data_status = "loaded" if ai_agent.bootstrap_data else "not_loaded"
    
    return {
        "status": "ok",
        "ai_agent_version": "2.0.0",
        "model_status": model_status,
        "data_status": data_status,
        "current_gameweek": ai_agent.current_gameweek,
        "models_available": list(ai_agent.models.keys()) if ai_agent.models else [],
        "capabilities": [
            "player_predictions",
            "transfer_recommendations", 
            "captain_analysis",
            "market_analysis",
            "fixture_planning",
            "risk_assessment"
        ],
        "database_connected": ai_agent.db_engine is not None
    }

def generate_ai_summary(analysis_results: dict, risk_tolerance: str) -> str:
    """Generate AI-powered summary of analysis"""
    summary_parts = []
    
    summary_parts.append(f"🤖 **AI Fantasy Analysis - GW {analysis_results.get('gameweek', 'N/A')}**")
    
    if "transfers" in analysis_results.get("recommendations", {}):
        transfer_count = len(analysis_results["recommendations"]["transfers"])
        if transfer_count > 0:
            top_transfer = analysis_results["recommendations"]["transfers"][0]
            summary_parts.append(f"🔄 **Top Transfer**: {top_transfer['player_in']} (+{top_transfer['predicted_points_gain']:.1f} pts)")
        summary_parts.append(f"📈 **Transfer Targets**: {transfer_count} AI-recommended options")
    
    if "captain" in analysis_results.get("recommendations", {}):
        captains = analysis_results["recommendations"]["captain"]
        if captains:
            top_captain = captains[0]
            summary_parts.append(f"⚡ **Captain Pick**: {top_captain['player']} ({top_captain['predicted_points']:.1f} pts)")
    
    if "differentials" in analysis_results.get("recommendations", {}):
        diff_count = len(analysis_results["recommendations"]["differentials"])
        if diff_count > 0:
            summary_parts.append(f"💎 **Differentials**: {diff_count} low-owned gems identified")
    
    # Add model confidence info
    model_confidence = analysis_results.get("model_confidence", "medium")
    summary_parts.append(f"🎯 **Model Confidence**: {model_confidence.upper()}")
    
    # Risk tolerance
    risk_emoji = {"low": "🛡️", "medium": "⚖️", "high": "🎲"}
    summary_parts.append(f"{risk_emoji.get(risk_tolerance, '⚖️')} **Risk Profile**: {risk_tolerance.upper()}")
    
    # Market insights
    if "insights" in analysis_results and "market_trends" in analysis_results["insights"]:
        market_data = analysis_results["insights"]["market_trends"]
        if "price_changes" in market_data:
            price_changes = len(market_data["price_changes"])
            summary_parts.append(f"💰 **Market Activity**: {price_changes} price changes detected")
    
    summary_parts.append("🚀 **Powered by**: Machine Learning predictions on 9 seasons of data")
    
    return "\n".join(summary_parts)

def generate_transfer_reasoning(pred, player_data: dict) -> str:
    """Generate reasoning for transfer recommendations"""
    reasons = []
    
    if pred.value_score > 3.0:
        reasons.append("exceptional value")
    elif pred.value_score > 2.0:
        reasons.append("good value")
    
    if pred.prediction_confidence > 0.8:
        reasons.append("high confidence prediction")
    
    if pred.risk_score < 0.3:
        reasons.append("low risk")
    elif pred.risk_score > 0.7:
        reasons.append("high risk")
    
    if float(player_data.get('selected_by_percent', 0)) < 5:
        reasons.append("differential pick")
    
    return f"AI recommends due to {', '.join(reasons)}. Predicted {pred.predicted_points:.0f} points."