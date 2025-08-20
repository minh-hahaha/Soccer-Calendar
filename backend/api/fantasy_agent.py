from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from .ai_agent import FantasyAdviceType, FantasyFootballAgent

router = APIRouter()

fantasy_agent = FantasyFootballAgent()

@router.get("/analyze")
def analyze_fantasy_strategy(
    analysis_types: str = Query("transfers,captain,differential", description="Comma-separated analysis types"),
    budget: float = Query(100.0, description="Available budget in millions"),
    gameweeks_ahead: int = Query(5, description="Number of gameweeks to analyze ahead"),
    current_team: Optional[str] = Query(None, description="Comma-separated player IDs (current team)")
):
    """
    Get comprehensive Fantasy Football analysis and recommendations
    """
    # Parse analysis types
    requested_types = []
    for analysis_type in analysis_types.split(","):
        analysis_type = analysis_type.strip()
        if analysis_type in [e.value for e in FantasyAdviceType]:
            requested_types.append(FantasyAdviceType(analysis_type))
    
    if not requested_types:
        requested_types = [FantasyAdviceType.TRANSFER, FantasyAdviceType.CAPTAIN]
    
    # Parse current team if provided
    current_team_ids = None
    if current_team:
        try:
            current_team_ids = [int(x.strip()) for x in current_team.split(",")]
        except:
            current_team_ids = None
    
    return fantasy_agent.analyze_fantasy_strategy(
        analysis_types=requested_types,
        budget=budget,
        current_team=current_team_ids,
        gameweeks_ahead=gameweeks_ahead
    )

@router.get("/captain-analysis")
def get_captain_analysis(
    gameweeks_ahead: int = Query(1, description="Gameweeks to analyze")
):
    """Get detailed captain analysis"""
    if not fantasy_agent.bootstrap_data:
        fantasy_agent.initialize_data()
    
    return {
        "captain_options": fantasy_agent._analyze_captain_options(gameweeks_ahead),
        "gameweek": fantasy_agent.current_gameweek,
        "analysis_type": "captain_focus"
    }

@router.get("/transfer-targets")
def get_transfer_targets(
    budget: float = Query(100.0), 
    position: Optional[str] = Query(None)
):
    """Get transfer targets by position"""
    if not fantasy_agent.bootstrap_data:
        fantasy_agent.initialize_data()
    
    transfers = fantasy_agent._analyze_transfers(budget)
    
    if position:
        # Filter by position if specified
        position_map = {"gkp": "Goalkeeper", "def": "Defender", "mid": "Midfielder", "fwd": "Forward"}
        target_position = position_map.get(position.lower())
        if target_position:
            # Would need to filter transfers by position
            pass
    
    return {
        "transfer_targets": transfers,
        "budget": budget,
        "gameweek": fantasy_agent.current_gameweek
    }

@router.get("/market-watch")
def get_market_insights():
    """Get current FPL market insights"""
    if not fantasy_agent.bootstrap_data:
        fantasy_agent.initialize_data()
    
    return {
        "market_insights": fantasy_agent._get_market_insights(),
        "gameweek": fantasy_agent.current_gameweek,
        "last_updated": datetime.utcnow().isoformat()
    }

@router.get("/differentials")
def get_differential_picks(
    max_ownership: float = Query(5.0, description="Maximum ownership percentage")
):
    """Get differential pick recommendations"""
    if not fantasy_agent.bootstrap_data:
        fantasy_agent.initialize_data()
    
    return {
        "differentials": fantasy_agent._analyze_differential_picks(),
        "max_ownership": max_ownership,
        "gameweek": fantasy_agent.current_gameweek
    }

@router.get("/health")
def fantasy_agent_health():
    """Health check for fantasy agent"""
    return {
        "status": "ok",
        "agent_version": "1.0.0",
        "data_initialized": fantasy_agent.bootstrap_data is not None,
        "current_gameweek": fantasy_agent.current_gameweek,
        "capabilities": [e.value for e in FantasyAdviceType]
    }

