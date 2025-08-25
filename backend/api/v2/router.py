# backend/api/v2/router.py
"""
Complete V2 API Router - AI Fantasy Football
Includes all your original endpoints plus the new architecture
"""
from datetime import datetime
from typing import Optional, List
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from ...services.ml_service import MLService
from ...core.config import get_settings
from .fantasy_agent import FantasyFootballAgent

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize the fantasy agent globally (your original approach)
fantasy_agent = FantasyFootballAgent(settings.DATABASE_URL)


# Pydantic models for request/response  
class TrainModelRequest(BaseModel):
    retrain: bool = False
    seasons_to_include: List[str] = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]


@router.get("/health")
async def ai_health_check():
    """Health check for AI services"""
    ml_service = MLService()
    health_status = ml_service.health_check()
    
    return {
        "status": "healthy" if health_status['healthy'] else "unhealthy",
        "service": "Enhanced ML Service",
        "details": health_status
    }


@router.get("/model-status")
async def get_model_status():
    """Get current model status and performance metrics"""
    if not fantasy_agent.models:
        # Try to load existing models
        if not fantasy_agent.load_models():
            return {
                "status": "not_trained",
                "message": "Models need to be trained first",
                "models_available": [],
                "last_trained": None
            }
    
    performance_report = fantasy_agent.get_model_performance_report()
    
    return {
        "status": "ready",
        "models_available": list(fantasy_agent.models.keys()),
        "performance": performance_report,
        "data_initialized": fantasy_agent.bootstrap_data is not None,
        "current_gameweek": fantasy_agent.current_gameweek
    }


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
    if not fantasy_agent.models:
        # Try to load models
        if not fantasy_agent.load_models():
            raise HTTPException(status_code=503, detail="AI models not available. Train models first.")
    
    if not fantasy_agent.bootstrap_data:
        if not fantasy_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize current season data")
    
    # Parse current team
    try:
        current_team_ids = [int(x.strip()) for x in current_team.split(",")]
    except:
        raise HTTPException(status_code=400, detail="Invalid current team format")
    
    # Parse analysis types
    requested_types = [t.strip() for t in analysis_types.split(",")]
    
    analysis_results = {
        "gameweek": fantasy_agent.current_gameweek,
        "analysis_timestamp": datetime.now().isoformat(),
        "ai_powered": True,
        "model_confidence": "high" if fantasy_agent.model_performance and min(fantasy_agent.model_performance.values(), key=lambda x: x['r2'])['r2'] > 0.3 else "medium",
        "recommendations": {},
        "insights": {
            "market_trends": fantasy_agent._get_market_insights() if hasattr(fantasy_agent, '_get_market_insights') else {},
            "ai_summary": ""
        }
    }
    
    # AI Transfer Analysis
    if "transfers" in requested_types:
        transfer_recs = fantasy_agent.get_ai_transfer_recommendations(current_team_ids, budget)
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
        captain_recs = fantasy_agent.get_ai_captain_recommendations(gameweeks_ahead)
        analysis_results["recommendations"]["captain"] = captain_recs
    
    # AI Differential Picks
    if "differential" in requested_types:
        analysis_results["recommendations"]["differentials"] = fantasy_agent.get_ai_differential_picks(risk_tolerance)
    
    # Generate AI summary
    analysis_results["insights"]["ai_summary"] = generate_ai_summary(analysis_results, risk_tolerance)
    
    return analysis_results


@router.post("/train-models")
async def train_ai_models(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks
):
    """Train or retrain the AI models (runs in background)"""
    def train_models():
        try:
            fantasy_agent.initialize_data()
            if request.retrain or not fantasy_agent.models:
                fantasy_agent.train_prediction_models()
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


@router.get("/player-predictions")
async def get_player_predictions(
    player_ids: Optional[str] = Query(None, description="Comma-separated player IDs, if None returns top predictions"),
    position: Optional[str] = Query(None, description="Filter by position: GKP, DEF, MID, FWD"),
    min_minutes: int = Query(200, description="Minimum minutes played"),
    limit: int = Query(20, description="Maximum number of players to return")
):
    """Get AI predictions for specific players or top performers"""
    
    if not fantasy_agent.models:
        if not fantasy_agent.load_models():
            raise HTTPException(status_code=503, detail="AI models not available")
    
    if not fantasy_agent.bootstrap_data:
        if not fantasy_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize data")
    
    players = fantasy_agent.bootstrap_data['elements']
    
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
            pred = fantasy_agent.predict_player_performance(player)
            predictions.append({
                "player_id": pred.player_id,
                "name": pred.name,
                "team": fantasy_agent._get_team_name(player['team']),
                "position": fantasy_agent._get_position_name(player['element_type']),
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
            logger.warning(f"Prediction failed for player {player.get('id')}: {str(e)}")
            continue
    
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
            "confidence": "high" if fantasy_agent.model_performance and min(fantasy_agent.model_performance.values(), key=lambda x: x['r2'])['r2'] > 0.3 else "medium",
            "last_trained": datetime.now().isoformat()
        }
    }


@router.get("/transfer-targets")
async def get_ai_transfer_targets(
    position: Optional[str] = Query(None, description="Position filter: GKP, DEF, MID, FWD"),
    max_price: float = Query(15.0, description="Maximum price"),
    min_predicted_points: float = Query(10.0, description="Minimum predicted points"),
    risk_level: str = Query("medium", description="Max risk level: low, medium, high"),
    limit: int = Query(10, description="Number of targets to return")
):
    """Get AI-recommended transfer targets"""
    
    if not fantasy_agent.models:
        if not fantasy_agent.load_models():
            raise HTTPException(status_code=503, detail="AI models not available")
    
    if not fantasy_agent.bootstrap_data:
        if not fantasy_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize data")
    
    players = fantasy_agent.bootstrap_data['elements']
    
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
            pred = fantasy_agent.predict_player_performance(player)
            
            if pred.predicted_points >= min_predicted_points and pred.risk_score <= max_risk:
                transfer_targets.append({
                    "player_id": pred.player_id,
                    "name": pred.name,
                    "team": fantasy_agent._get_team_name(player['team']),
                    "position": fantasy_agent._get_position_name(player['element_type']),
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
    
    # Sort by AI rating
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
    
    if not fantasy_agent.models:
        if not fantasy_agent.load_models():
            raise HTTPException(status_code=503, detail="AI models not available")
    
    if not fantasy_agent.bootstrap_data:
        if not fantasy_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize data")
    
    captain_analysis = fantasy_agent.get_ai_captain_recommendations(gameweeks_ahead)
    
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
    
    if not fantasy_agent.bootstrap_data:
        if not fantasy_agent.initialize_data():
            raise HTTPException(status_code=503, detail="Failed to initialize data")
    
    players = fantasy_agent.bootstrap_data['elements']
    
    # Market trends analysis
    price_risers = []
    price_fallers = []
    undervalued_picks = []
    overvalued_picks = []
    
    for player in players:
        if player.get('minutes', 0) < 50:
            continue
            
        try:
            if fantasy_agent.models:
                pred = fantasy_agent.predict_player_performance(player)
                
                # Price change analysis
                if player.get('cost_change_event', 0) > 0:
                    price_risers.append({
                        "name": f"{player['first_name']} {player['second_name']}",
                        "team": fantasy_agent._get_team_name(player['team']),
                        "price_change": player['cost_change_event'] / 10,
                        "new_price": player['now_cost'] / 10,
                        "predicted_points": round(pred.predicted_points, 1),
                        "ai_value_score": round(pred.value_score, 2)
                    })
                elif player.get('cost_change_event', 0) < 0:
                    price_fallers.append({
                        "name": f"{player['first_name']} {player['second_name']}",
                        "team": fantasy_agent._get_team_name(player['team']),
                        "price_change": player['cost_change_event'] / 10,
                        "new_price": player['now_cost'] / 10,
                        "predicted_points": round(pred.predicted_points, 1),
                        "potential_bargain": bool(pred.value_score > 2.0) 
                    })
                
                # Value analysis
                current_value = player['total_points'] / (player['now_cost'] / 10)
                predicted_value = pred.predicted_points / (player['now_cost'] / 10)
                
                if predicted_value > current_value * 1.2 and float(player.get('selected_by_percent', 0)) < 10:
                    undervalued_picks.append({
                        "name": f"{player['first_name']} {player['second_name']}",
                        "team": fantasy_agent._get_team_name(player['team']),
                        "current_value": round(current_value, 2),
                        "predicted_value": round(predicted_value, 2),
                        "upside": round((predicted_value - current_value) / current_value * 100, 1),
                        "ownership": float(player.get('selected_by_percent', 0)),
                        "confidence": round(pred.prediction_confidence, 3)
                    })
        except:
            continue
    
    # Sort results
    price_risers.sort(key=lambda x: abs(x['price_change']), reverse=True)
    price_fallers.sort(key=lambda x: abs(x['price_change']), reverse=True)
    undervalued_picks.sort(key=lambda x: x['upside'], reverse=True)
    
    return {
        "market_analysis": {
            "price_risers": price_risers[:10],
            "price_fallers": price_fallers[:10],
            "undervalued_gems": undervalued_picks[:10],
        },
        "ai_insights": {
            "market_sentiment": "bullish" if len(price_risers) > len(price_fallers) else "bearish",
            "value_opportunities": len(undervalued_picks),
        },
        "analysis_timestamp": datetime.now().isoformat(),
        "gameweek": fantasy_agent.current_gameweek
    }


# Helper functions
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
    
    # Add model confidence info
    model_confidence = analysis_results.get("model_confidence", "medium")
    summary_parts.append(f"🎯 **Model Confidence**: {model_confidence.upper()}")
    
    summary_parts.append("🚀 **Powered by**: Machine Learning predictions on historical data")
    
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
    
    if float(player_data.get('selected_by_percent', 0)) < 5:
        reasons.append("differential pick")
    
    return f"AI recommends due to {', '.join(reasons)}. Predicted {pred.predicted_points:.0f} points."