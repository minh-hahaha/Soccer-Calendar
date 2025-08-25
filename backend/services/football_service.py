"""Football Data Service"""
import logging
import requests
from typing import List, Dict, Any, Optional
from ..core.config import get_settings
from ..core.exceptions import ServiceError
from ..core.database import get_db_session
from ..models.database.football import Match, Team, Standing

logger = logging.getLogger(__name__)
settings = get_settings()


class FootballService:
    """Service for football data operations"""
    
    def __init__(self):
        self.settings = settings
        self.api_headers = {"X-Auth-Token": settings.FD_API_KEY}
    
    def fetch_fixtures(self, season: str = "2025") -> List[Dict[str, Any]]:
        """Fetch fixtures from Football Data API"""
        try:
            url = f"{settings.FD_API_BASE_URL}/competitions/PL/matches"
            params = {"season": season}
            
            response = requests.get(url, headers=self.api_headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return self.clean_match_data(data.get("matches", []))
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch fixtures: {str(e)}")
            raise ServiceError(f"Failed to fetch fixtures: {str(e)}")
    
    def clean_match_data(self, raw_matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean match data"""
        cleaned = []
        for match in raw_matches:
            cleaned.append({
                "id": match.get("id"),
                "date": match.get("utcDate"),
                "home_team": self.normalize_team_name(match.get("homeTeam", {}).get("shortName", "")),
                "away_team": self.normalize_team_name(match.get("awayTeam", {}).get("shortName", "")),
                "home_score": match.get("score", {}).get("fullTime", {}).get("home"),
                "away_score": match.get("score", {}).get("fullTime", {}).get("away"),
                "matchday": match.get("matchday"),
                "status": match.get("status"),
                "home_team_crest": match.get("homeTeam", {}).get("crest"),
                "away_team_crest": match.get("awayTeam", {}).get("crest"),
            })
        return cleaned
    
    def normalize_team_name(self, name: str) -> str:
        """Normalize team names"""
        if not name:
            return name
        return name.replace(" FC", "").strip()
    
    def store_matches(self, matches: List[Dict[str, Any]], season: int = 2025):
        """Store matches in database"""
        try:
            with get_db_session() as db:
                # Clear existing matches for the season
                db.query(Match).filter(Match.season == season).delete()
                
                # Insert new matches
                for match_data in matches:
                    match = Match(
                        id=match_data["id"],
                        date=match_data["date"],
                        home_team=match_data["home_team"],
                        away_team=match_data["away_team"],
                        home_score=match_data["home_score"],
                        away_score=match_data["away_score"],
                        matchday=match_data["matchday"],
                        status=match_data["status"],
                        home_team_crest=match_data["home_team_crest"],
                        away_team_crest=match_data["away_team_crest"],
                        season=season
                    )
                    db.add(match)
                
                logger.info(f"Stored {len(matches)} matches for season {season}")
                
        except Exception as e:
            logger.error(f"Failed to store matches: {str(e)}")
            raise ServiceError(f"Failed to store matches: {str(e)}")