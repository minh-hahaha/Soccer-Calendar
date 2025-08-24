from typing import NoReturn
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, List, Any, Union
import requests
import os
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

router = APIRouter()


class FantasyAdviceType(str, Enum):
    TRANSFER = "transfers"
    CAPTAIN = "captain"
    DIFFERENTIAL = "differential"
    BUDGET_OPTIMIZATION = "budget_optimization"
    BENCH_STRATEGY = "bench_strategy"
    FIXTURE_PLANNING = "fixture_planning"


class Position (str, Enum):
    GKP = "Goalkeeper"
    DEF = "Defender"
    MID = "Midfielder"
    FWD = "Forward"


@dataclass
class FantasyPlayer:
    name: str
    team: str
    position: Position
    price: float
    total_points: int
    points_per_game: float
    selected_by_percent: float
    form: float
    minutes: int
    goals: int
    assists: int
    clean_sheets: int
    saves: int
    bonus_points: int
    price_change_week: float
    fixture_difficulty: float
    injury_risk: str
    upcoming_fixtures: List[str]


@dataclass
class TransferSuggestion:
    player_out: str
    player_in: str
    reason: str
    priority: str # High, Medium, Low
    points_potential: int
    risk_level: str # High, Medium, Low
    cost: float
    confidence: float


@dataclass
class CaptainSuggestion:
    player: str
    team: str
    opponent: str
    is_home: bool
    expected_points: float
    ceiling: float # best case scenario
    floor: float # worst case scenario
    reasoning: str
    confidence: float
    differential_factor: float # how much of a differential pick is this

class FantasyFootballAgent:
    """ AI Agent for Fantasy Football Analysis and recommendations"""

    def __init__(self, fpl_api_base : str = "https://fantasy.premierleague.com/api/"):
        self.fpl_api_base = fpl_api_base
        self.current_gameweek = None
        self.bootstrap_data = None
        self.fixtures_data = None
    
    def initialize_data(self):
        """ Initialize FPL data - call before analysis"""
        try:
            print("Fetching fresh data from FPL API...")
            
            # get bootstrap data (players, teams, gameweeks)
            bootstrap_response = requests.get(f"{self.fpl_api_base}/bootstrap-static/")
            if bootstrap_response.status_code == 200:
                self.bootstrap_data = bootstrap_response.json()

                # find current gameweek
                self.current_gameweek = self._find_current_gameweek()
                
                # get fixtures data
                fixtures_response = requests.get(f"{self.fpl_api_base}/fixtures/")
                if fixtures_response.status_code == 200:
                    self.fixtures_data = fixtures_response.json()
                    
                return True
        except Exception as e:
            print(f"Error initializing data: {e}")
            return False
    
    def _find_current_gameweek(self) -> Optional[int]:
        """Find current gameweek from bootstrap data"""
        if not self.bootstrap_data:
            return None
        
        for gw in self.bootstrap_data["events"]:
            if gw["is_current"]:
                return gw["id"]
        return None

    def analyze_fantasy_strategy(self, analysis_types: List[FantasyAdviceType], 
                                budget: float = 100.0,
                                current_team: Optional[List[int]] = None,
                                gameweeks_ahead: int = 5) -> Dict[str, Any]:
        """ Main entry point for fantasy analysis"""
        if not self.bootstrap_data:
            if not self.initialize_data():
                raise HTTPException(status_code=500, detail="Failed to initialize data")
        
        analysis_results = {
            "gameweek": self.current_gameweek,
            "analysis_timestamp": datetime.now().isoformat(),
            "budget": budget,
            "gameweeks_analyzed": gameweeks_ahead,
            "recommendations": {},
            "market_insights": self._get_market_insights(),
            "agent_summary": ""
        }

        for analysis_type in analysis_types:
            if analysis_type == FantasyAdviceType.TRANSFER:
                analysis_results["recommendations"]["transfers"] = self._analyze_transfers(budget, current_team)
            elif analysis_type == FantasyAdviceType.CAPTAIN:
                analysis_results["recommendations"]["captain"] = self._analyze_captain_options(gameweeks_ahead)
            elif analysis_type == FantasyAdviceType.DIFFERENTIAL:
                analysis_results["recommendations"]["differentials"] = self._analyze_differential_picks()
            elif analysis_type == FantasyAdviceType.BUDGET_OPTIMIZATION:
                analysis_results["recommendations"]["budget"] = self._analyze_budget_optimization(budget)
            elif analysis_type == FantasyAdviceType.FIXTURE_PLANNING:
                analysis_results["recommendations"]["fixtures"] = self._analyze_fixture_planning(gameweeks_ahead)

        # Generate overall agent summary
        analysis_results["agent_summary"] = self._generate_fantasy_summary(analysis_results)
        
        return analysis_results

    def _get_market_insights(self) -> Dict[str, Any]:
        """Analyze current FPL market trends"""
        if not self.bootstrap_data:
            return {}

        players = self.bootstrap_data["elements"]

        # price risers and fallers
        price_changes = []
        for player in players:
            if abs(player["cost_change_event"]) > 0:
                price_changes.append({
                    "name": f"{player['first_name']} {player['second_name']}",
                    "team": self._get_team_name(player["team"]),
                    "change": player["cost_change_event"] / 10, 
                    "new_price": player["now_cost"] / 10,
                    "selected_by_percent": player["selected_by_percent"],
                })

        # most transferred in/out
        transfers_in = sorted(players, key = lambda x: x.get("transfers_in_event",0), reverse = True) [:5]
        transfers_out = sorted(players, key = lambda x: x.get("transfers_out_event",0), reverse = True) [:5]

        # top scorers
        top_scorers = sorted(players, key = lambda x: x.get("total_points",0), reverse = True) [:5]

        return {
            "price_changes": sorted(price_changes, key=lambda x: abs(x["change"]), reverse=True)[:10],
            "transfers_in": [self._player_summary(p) for p in transfers_in],
            "transfers_out": [self._player_summary(p) for p in transfers_out],
            "top_scorers": [self._player_summary(p) for p in top_scorers]
        }

    def _analyze_transfers(self, budget: float, current_team: Optional[List[int]] = None) -> List[TransferSuggestion]:
            """Analyze best transfer opportunities"""
            if not self.bootstrap_data:
                return []
            
            players = self.bootstrap_data["elements"]
            transfer_suggestions = []

            #analyze by position
            for position_id in range(1,5): #GK, DF, MD, FW
                position_players = [p for p in players if p["element_type"] == position_id]

                # sort by value (points per million)
                for player in sorted(position_players, key = lambda x: self._calculate_value_score(x), reverse = True)[:3]:

                    # check if it is good transfer target
                    value_score = self._calculate_value_score(player)
                    fixture_score = self._calculate_fixture_difficulty(player["team"])
                    form_score = float(player.get("form", 0))

                    if value_score > 1.5 and form_score > 3: # ARBITRARY THRESHOLDS
                        suggestion = TransferSuggestion(
                            player_out="TBD", # would need current team data to determine
                            player_in = f"{player['first_name']} {player['second_name']}",
                            reason = self._generate_transfer_reasoning(player, value_score, fixture_score, form_score),
                            priority = "HIGH" if value_score > 2.5 else "Medium",
                            points_potential = int(float(player.get("ep_next", 0)) * 5), #5 week projection
                            risk_level = "LOW" if player["minutes"] > 500 else "Medium",
                            cost = player["now_cost"] / 10,
                            confidence = min(0.9, (value_score / 3) + (form_score/ 10))
                        )

                        transfer_suggestions.append(suggestion)

            return sorted(transfer_suggestions, key = lambda x: x.confidence, reverse = True) [:8]
            

    def _analyze_captain_options(self, gameweeks_ahead: int = 1) -> List[CaptainSuggestion]:
            """Analyze best captain options"""
            if not self.bootstrap_data:
                return []
            
            players = self.bootstrap_data["elements"]
            captain_suggestions = []

            # Focus on premium players (high ownership/price)
            premium_players = [p for p in players if p["now_cost"] >= 80 and float(p["selected_by_percent"]) >= 15]

            for player in premium_players:
                # get next fixture
                next_fixture = self._get_next_fixture(player["team"])
                if not next_fixture:
                    continue
                
               # calculate captain metrics
                expected_points = float(player.get("ep_next", 0))
                form = float(player.get("form", 0))
                fixture_difficulty = self._calculate_fixture_difficulty_for_match(next_fixture)

                # adjust for fixture difficulty
                adjusted_points = expected_points * (6 - fixture_difficulty)/3

                # calculate ceiling and floor
                ceiling = adjusted_points * 1.8 # best case
                floor = max(1, adjusted_points * 0.3) # worst case

                # differential factor
                ownership = float(player["selected_by_percent"])
                differential_factor = max(0, (50 - ownership) / 50)

                suggestion = CaptainSuggestion(
                    player = f"{player['first_name']} {player['second_name']}",
                    team = self._get_team_name(player["team"]),
                    opponent = self._get_opponent_name(next_fixture, player["team"]),
                    is_home = self._is_home_fixture(next_fixture, player["team"]),
                    expected_points = adjusted_points,
                    ceiling = ceiling,
                    floor = floor,
                    reasoning=self._generate_captain_reasoning(player, next_fixture, form, fixture_difficulty),
                    confidence=min(0.95, (form / 5) + (adjusted_points / 15)),
                    differential_factor = differential_factor
                )

                captain_suggestions.append(suggestion)

            return sorted(captain_suggestions, key = lambda x: x.expected_points, reverse = True) [:6]
        
    
    def _analyze_differential_picks(self) -> List[Dict[str, Any]]:
            """Find low-owned players with high potential"""

            if not self.bootstrap_data:
                return []
            
            players = self.bootstrap_data["elements"]
            differentials = []


            for player in players:
                ownership = float(player["selected_by_percent"])
                if ownership < 5.0 and player["minutes"] > 85:  # Lower threshold for early season
                    value_score = self._calculate_value_score(player)
                    form = float(player.get("form", 0))

                    if value_score > 1.2 and form > 3: # ARBITRARY THRESHOLDS
                        differentials.append({
                            "name": f"{player['first_name']} {player['second_name']}",
                            "team": self._get_team_name(player["team"]),
                            "position": self._get_position_name(player["element_type"]),
                            "price": player["now_cost"] / 10,
                            "ownership": ownership,
                            "form": form,
                            "value_score": value_score,
                            "reasoning": f"Low ownership ({ownership}%) with strong form and value. Could be a great differential pick.",
                            "risk_level": "MEDIUM" if player["minutes"] > 600 else "HIGH"
                        })

            return sorted(differentials, key = lambda x: x["value_score"], reverse = True) [:5]
    
    def _analyze_budget_optimization(self, budget: float) -> List[Dict[str, Any]]:
            """Optimize team budget allocation"""
            if not self.bootstrap_data:
                return []
            
            players = self.bootstrap_data["elements"]
            
            # analyze spending by position

            position_analysis = {}

            for pos_id in range(1,5):
                pos_players = [p for p in players if p["element_type"] == pos_id]
                pos_name = self._get_position_name(pos_id)

                # find optimal price ranges
                sorted_by_value = sorted(pos_players, key = lambda x: self._calculate_value_score(x), reverse = True)

                position_analysis[pos_name] = {
                    "recommended_budget": self._calculate_recommended_budget(pos_id, budget),
                    "sweet_spot_range": self._find_sweet_spot_price_range(sorted_by_value),
                    "top_value_picks": [self._player_summary(p) for p in sorted_by_value[:3]]
                }

            return {
                "total_budget": budget,
                "position_breakdown": position_analysis,
                "strategy": "Focus premium spend on midfield and forwards, save money on defenders and goalkeepers"
            }

    def _analyze_fixture_planning(self, gameweeks_ahead: int) -> List[Dict[str, Any]]:
            """Analyze fixture difficulty for upcoming gameweeks"""
            if not self.bootstrap_data or not self.fixtures_data:
                return []
            
            teams = self.bootstrap_data["teams"]
            fixture_analysis = {}

            for team in teams:
                team_fixtures = self._get_team_fixtures(team["id"], gameweeks_ahead)
                difficulty_scores = [self._calculate_fixture_difficulty_for_match(f) for f in team_fixtures]

                fixture_analysis[team["name"]] = {
                    "average_difficulty": statistics.mean(difficulty_scores) if difficulty_scores else 5,
                    "fixtures": len(team_fixtures),
                    "home_fixtures": sum(1 for f in team_fixtures if self._is_home_fixture(f, team["id"])),
                    "recommendation": self._get_fixture_recommendation(difficulty_scores)
                }

            # Sort by best fixtures
            best_fixtures = sorted(fixture_analysis.items(), key=lambda x: x[1]["average_difficulty"])
            
            return {
                "gameweeks_analyzed": gameweeks_ahead,
                "best_fixture_runs": best_fixtures[:5],
                "worst_fixture_runs": best_fixtures[-5:],
                "double_gameweeks": [],  # Would need to check for DGWs
                "blank_gameweeks": []    # Would need to check for BGWs
            }    
        

        ## HELPER FUNCTIONS

          # Helper methods
    def _calculate_value_score(self, player: Dict) -> float:
        """Calculate value score (points per million)"""
        price = player["now_cost"] / 10
        total_points = player["total_points"]
        return (total_points / price) if price > 0 else 0

    def _calculate_fixture_difficulty(self, team_id: int) -> float:
        """Calculate average fixture difficulty for a team"""
        # Simplified - would normally look at actual upcoming fixtures
        return 3.0  # Default medium difficulty

    def _calculate_fixture_difficulty_for_match(self, fixture: Dict) -> int:
        """Calculate difficulty for a specific fixture"""
        # Simplified - would use team strength ratings
        return fixture.get("difficulty", 3)

    def _get_team_name(self, team_id: int) -> str:
        """Get team name from team ID"""
        if self.bootstrap_data:
            for team in self.bootstrap_data["teams"]:
                if team["id"] == team_id:
                    return team["short_name"]
        return f"Team {team_id}"

    def _get_position_name(self, position_id: int) -> str:
        """Convert position ID to name"""
        positions = {1: "Goalkeeper", 2: "Defender", 3: "Midfielder", 4: "Forward"}
        return positions.get(position_id, "Unknown")

    def _get_next_fixture(self, team_id: int) -> Optional[Dict]:
        """Get next fixture for a team"""
        if not self.fixtures_data:
            return None
        
        upcoming = [f for f in self.fixtures_data 
                   if (f["team_h"] == team_id or f["team_a"] == team_id) 
                   and not f["finished"] and f["event"] is not None]
        
        return sorted(upcoming, key=lambda x: x["event"])[0] if upcoming else None

    def _get_opponent_name(self, fixture: Dict, team_id: int) -> str:
        """Get opponent name from fixture"""
        opponent_id = fixture["team_a"] if fixture["team_h"] == team_id else fixture["team_h"]
        return self._get_team_name(opponent_id)

    def _is_home_fixture(self, fixture: Dict, team_id: int) -> bool:
        """Check if fixture is at home"""
        return fixture["team_h"] == team_id

    def _get_team_fixtures(self, team_id: int, gameweeks: int) -> List[Dict]:
        """Get upcoming fixtures for a team"""
        if not self.fixtures_data:
            return []
        
        current_gw = self.current_gameweek or 1
        upcoming = [f for f in self.fixtures_data 
                   if (f["team_h"] == team_id or f["team_a"] == team_id) 
                   and not f["finished"] 
                   and f["event"] is not None 
                   and f["event"] <= current_gw + gameweeks]
        
        return sorted(upcoming, key=lambda x: x["event"])

    def _player_summary(self, player: Dict) -> Dict[str, Any]:
        """Create player summary"""
        return {
            "name": f"{player['first_name']} {player['second_name']}",
            "team": self._get_team_name(player["team"]),
            "position": self._get_position_name(player["element_type"]),
            "price": player["now_cost"] / 10,
            "points": player["total_points"],
            "form": player.get("form", 0),
            "selected_by": player["selected_by_percent"]
        }

    def _generate_transfer_reasoning(self, player: Dict, value_score: float, fixture_score: float, form_score: float) -> str:
        """Generate reasoning for transfer suggestion"""
        reasons = []
        if value_score > 2.0:
            reasons.append("excellent value for money")
        if form_score > 4:
            reasons.append("strong recent form")
        if fixture_score < 3:
            reasons.append("favorable upcoming fixtures")
        
        return f"Strong pick due to {' and '.join(reasons)}."

    def _generate_captain_reasoning(self, player: Dict, fixture: Dict, form: float, difficulty: int) -> str:
        """Generate reasoning for captain suggestion"""
        player_name = f"{player['first_name']} {player['second_name']}"
        opponent = self._get_opponent_name(fixture, player["team"])
        home_away = "home" if self._is_home_fixture(fixture, player["team"]) else "away"
        
        return f"{player_name} faces {opponent} at {home_away}. Good form ({form}) and favorable fixture difficulty."

    def _calculate_recommended_budget(self, position_id: int, total_budget: float) -> float:
        """Calculate recommended budget allocation by position"""
        allocations = {1: 0.1, 2: 0.25, 3: 0.35, 4: 0.3}  # GKP, DEF, MID, FWD
        return total_budget * allocations.get(position_id, 0.25)

    def _find_sweet_spot_price_range(self, players: List[Dict]) -> Dict[str, float]:
        """Find the price range with best value"""
        # Simplified - would do more complex analysis
        return {"min": 5.0, "max": 8.0}

    def _get_fixture_recommendation(self, difficulty_scores: List[int]) -> str:
        """Get recommendation based on fixture difficulty"""
        if not difficulty_scores:
            return "No upcoming fixtures"
        
        avg_difficulty = statistics.mean(difficulty_scores)
        if avg_difficulty <= 2.5:
            return "STRONG BUY - Excellent fixtures"
        elif avg_difficulty <= 3.5:
            return "CONSIDER - Decent fixtures"
        else:
            return "AVOID - Difficult fixtures"

    def _generate_fantasy_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate overall fantasy strategy summary"""
        summary = f"🎯 **Fantasy Football Agent - Gameweek {analysis['gameweek']} Analysis**\n\n"
        
        if "transfers" in analysis["recommendations"]:
            transfer_count = len(analysis["recommendations"]["transfers"])
            summary += f"**Transfer Opportunities:** {transfer_count} high-value targets identified\n"
        
        if "captain" in analysis["recommendations"]:
            captain_count = len(analysis["recommendations"]["captain"])
            top_captain = analysis["recommendations"]["captain"][0].player if captain_count > 0 else "None"
            summary += f"**Captain Recommendation:** {top_captain}\n"
        
        if "differentials" in analysis["recommendations"]:
            diff_count = len(analysis["recommendations"]["differentials"])
            summary += f"**Differential Picks:** {diff_count} low-owned gems found\n"
        
        summary += f"\n**Market Status:** Active with {len(analysis['market_insights'].get('price_changes', []))} price changes\n"
        summary += f"**Strategy Focus:** Maximize value while planning for upcoming fixture swings\n"
        
        return summary
        

