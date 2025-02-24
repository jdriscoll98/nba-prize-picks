import requests
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
import json
from pathlib import Path
import time
from hashlib import md5

class NBAApiWrapper:
    """
    A wrapper class for the RAPID API NBA API
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = ".cache", cache_ttl: int = 3600):
        """
        Initialize the NBA API wrapper
        
        Args:
            api_key (str, optional): The API key for authentication
            cache_dir (str): Directory to store cache files
            cache_ttl (int): Cache time-to-live in seconds (default 1 hour)
        """
        load_dotenv()
        
        self.api_key = api_key or os.getenv('RAPID_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided or set in environment variables as RAPID_API_KEY")
            
        self.base_url = "https://api-nba-v1.p.rapidapi.com"
        self.headers = {
            'x-rapidapi-host': 'api-nba-v1.p.rapidapi.com',
            'x-rapidapi-key': self.api_key
        }
        
        # Cache settings
        self.cache_dir = Path(cache_dir)
        self.cache_ttl = cache_ttl
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate a unique cache key for the request"""
        # Create a string combining endpoint and sorted params
        cache_str = endpoint
        if params:
            param_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
            cache_str = f"{endpoint}?{param_str}"
        
        # Create MD5 hash of the string for filename
        return md5(cache_str.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get response from cache if it exists and is valid"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is still valid
                if time.time() - cached_data['cached_at'] < self.cache_ttl:
                    return cached_data['data']
            except (json.JSONDecodeError, KeyError):
                pass
        
        return None

    def _save_to_cache(self, cache_key: str, data: Dict):
        """Save response to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        cache_data = {
            'cached_at': time.time(),
            'data': data
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Make a GET request to the API with caching
        
        Args:
            endpoint (str): The API endpoint to call
            params (dict, optional): Query parameters to include in the request
            
        Returns:
            dict: The JSON response from the API
        """
        # Generate cache key
        cache_key = self._get_cache_key(endpoint, params)
        
        # Try to get from cache first
        cached_response = self._get_cached_response(cache_key)
        if cached_response is not None:
            return cached_response
        
        # If not in cache, make API request
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Save to cache
            self._save_to_cache(cache_key, data)
            
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def get_seasons(self) -> Dict:
        """Get all available seasons"""
        return self._make_request("seasons")

    def get_leagues(self) -> Dict:
        """Get all available leagues"""
        return self._make_request("leagues")

    def get_games(self, **params) -> Dict:
        """
        Get list of games based on provided parameters
        
        Possible parameters:
        - id (int): The game ID
        - date (str): Format YYYY-MM-DD
        - live (str): 'all' for live games
        - league (str): League name (e.g., 'standard')
        - season (int): Season year (YYYY)
        - team (int): Team ID
        - h2h (str): Two team IDs (e.g., '1-4')
        """
        return self._make_request("games", params)
    
    def save_all_games(self, season: Optional[int] = None, filename: str = "games.json"):
        """
        Fetch and save all NBA games to a file
        
        Args:
            season (int, optional): Season year YYYY
            filename (str): Name of file to save games to
        """
        games = self.get_games(season=season)
        with open(filename, 'w') as f:
            json.dump(games, f) 
    

    def get_teams(self, **params) -> Dict:
        """
        Get team data based on provided parameters
        
        Possible parameters:
        - id (int): Team ID
        - name (str): Team name
        - code (str): Team code (3 characters)
        - league (str): League name
        - conference (str): Conference name ('East' or 'West')
        - division (str): Division name
        - search (str): Search term (min 3 characters)
        """
        return self._make_request("teams", params)

    def get_players(self, **params) -> Dict:
        """
        Get player data based on provided parameters
        
        Possible parameters:
        - id (int): Player ID
        - name (str): Player name
        - team (int): Team ID
        - season (int): Season year (YYYY)
        - country (str): Player's country
        - search (str): Search term (min 3 characters)
        """
        return self._make_request("players", params)

    def get_standings(self, league: str, season: int, **params) -> Dict:
        """
        Get standings for a league and season
        
        Args:
            league (str): League name (required)
            season (int): Season year YYYY (required)
            **params: Additional parameters like team, conference, or division
        """
        params.update({
            'league': league,
            'season': season
        })
        return self._make_request("standings", params)

    def get_game_statistics(self, game_id: int) -> Dict:
        """
        Get statistics for a specific game
        
        Args:
            game_id (int): The ID of the game
        """
        return self._make_request("games/statistics", {'id': game_id})

    def get_team_statistics(self, team_id: int, season: int, stage: Optional[int] = None) -> Dict:
        """
        Get team statistics for a season
        
        Args:
            team_id (int): The ID of the team
            season (int): Season year YYYY
            stage (int, optional): The stage of the games
        """
        params = {
            'id': team_id,
            'season': season
        }
        if stage is not None:
            params['stage'] = stage
        return self._make_request("teams/statistics", params)

    def get_player_statistics(self, **params) -> Dict:
        """
        Get player statistics based on provided parameters
        
        Possible parameters:
        - id (int): Player ID
        - game (int): Game ID
        - team (int): Team ID
        - season (int): Season year YYYY
        """
        return self._make_request("players/statistics", params)

    def get_all_teams(self) -> Dict:
        """
        Get all NBA teams from the standard league.
        
        Returns:
            Dict: Response containing all NBA teams
        """
        east = [x for x in self.get_teams(league="standard", conference="East")['response'] if x['nbaFranchise'] and not x['allStar']]
        west = [x for x in self.get_teams(league="standard", conference="West")['response'] if x['nbaFranchise'] and not x['allStar']]
        return east + west

    def get_all_players(self, season: Optional[int] = None) -> List[Dict]:
        """
        Get all players from all teams
        
        Args:
            season (int, optional): Season year YYYY. If not provided, gets current players.
        
        Returns:
            List[Dict]: List of all players
        """
        teams = self.get_all_teams()
        all_players = []
        
        for team in teams:
            try:
                params = {'team': team['id']}
                if season:
                    params['season'] = season
                    
                response = self.get_players(**params)
                if response.get('response'):
                    all_players.extend(response['response'])
                    
            except Exception as e:
                print(f"Error fetching players for team {team.get('name', team.get('id'))}: {str(e)}")
                continue
                
        return all_players 

    def get_all_player_stats(self, season: Optional[int] = None) -> List[Dict]:
        """
        Get statistics for all NBA players (players with NBA experience)
        
        Args:
            season (int, optional): Season year YYYY. If not provided, gets current season stats.
        
        Returns:
            List[Dict]: List of player statistics
        """
        # First check if players.json exists and load from it
        players_file = Path("players.json")
        # If not, get all players and save to players.json
        nba_players = self.get_all_players(season=season)
        with open(players_file, 'w') as f:
            json.dump(nba_players, f)
        
        # Filter for NBA players (those with nba.start > 0)
        
        all_stats = []
        total_players = len(nba_players)
        
        print(f"Fetching stats for {total_players} NBA players...")
        
        for idx, player in enumerate(nba_players, 1):
            try:
                params = {'id': player['id']}
                if season:
                    params['season'] = season
                
                response = self.get_player_statistics(**params)
                if response.get('response'):
                    # Add player info to stats
                    stats = response['response']
                    all_stats.extend(stats)
                
                # Progress update
                if idx % 10 == 0:
                    print(f"Processed {idx}/{total_players} players...")
                    
            except Exception as e:
                print(f"Error fetching stats for player {player.get('firstname')} {player.get('lastname')}: {str(e)}")
                continue
        
        print(f"Completed fetching stats for {total_players} players")
        return all_stats

    def save_all_player_stats(self, season: Optional[int] = None, filename: str = "player_stats.json"):
        """
        Fetch and save all NBA player statistics to a file
        
        Args:
            season (int, optional): Season year YYYY
            filename (str): Name of file to save stats to
        """
        stats = self.get_all_player_stats(season=season)
        
        with open(filename, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Saved {len(stats)} player statistics to {filename}") 