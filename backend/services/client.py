import requests
import time
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from backend.config import settings


class FootballDataClient:
    def __init__(self):
        self.api_key = settings.fd_api_key
        self.base_url = settings.base_url
        self.rate_limit_delay = settings.rate_limit_delay
        self.last_request_time = 0
        
        # Create cache directory
        os.makedirs("cache", exist_ok=True)
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache file path"""
        param_str = "_".join([f"{k}_{v}" for k, v in sorted(params.items())])
        return f"cache/{endpoint}_{param_str}.json"
    
    def _load_cache(self, cache_path: str) -> Optional[Dict[str, Any]]:
        """Load cached response if available and not expired"""
        if not os.path.exists(cache_path):
            return None
        
        # Check if cache is less than 1 hour old
        if time.time() - os.path.getmtime(cache_path) > 3600:
            return None
        
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def _save_cache(self, cache_path: str, data: Dict[str, Any]):
        """Save response to cache"""
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        except:
            pass  # Ignore cache save errors
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with caching and rate limiting"""
        if params is None:
            params = {}
        
        cache_path = self._get_cache_path(endpoint, params)
        cached_data = self._load_cache(cache_path)
        if cached_data:
            return cached_data
        
        self._rate_limit()
        
        headers = {"X-Auth-Token": self.api_key}
        url = f"{self.base_url}/{endpoint}"
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            self._save_cache(cache_path, data)
            return data
        elif response.status_code == 429:
            # Rate limited, wait and retry
            time.sleep(60)
            return self._make_request(endpoint, params)
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def get_matches(self, season: int, competition_code: str = None) -> Dict[str, Any]:
        """Get matches for a season"""
        if competition_code is None:
            competition_code = settings.competition_code
        
        return self._make_request(f"competitions/{competition_code}/matches", {"season": season})
    
    def get_standings(self, season: int, competition_code: str = None) -> Dict[str, Any]:
        """Get standings for a season"""
        if competition_code is None:
            competition_code = settings.competition_code
        
        return self._make_request(f"competitions/{competition_code}/standings", {"season": season})
    
    def get_teams(self, competition_code: str = None) -> Dict[str, Any]:
        """Get teams for a competition"""
        if competition_code is None:
            competition_code = settings.competition_code
        
        return self._make_request(f"competitions/{competition_code}/teams")
    
    def get_match(self, match_id: int) -> Dict[str, Any]:
        """Get specific match details"""
        return self._make_request(f"matches/{match_id}")
    
    def get_team_matches(self, team_id: int, season: int = None) -> Dict[str, Any]:
        """Get matches for a specific team"""
        params = {}
        if season:
            params["season"] = season
        
        return self._make_request(f"teams/{team_id}/matches", params)
