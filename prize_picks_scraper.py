import requests
import http.client
from typing import Optional, Dict, List
import uuid
from datetime import datetime, date
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prizepicks_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PrizePicksAPI:
    """
    API wrapper for PrizePicks.com
    """
    
    LEAGUE_IDS = {
        'NBA': 7,
        # Add other leagues as needed
    }
    
    def __init__(self):
        """Initialize the PrizePicks API wrapper"""
        logger.info("Initializing PrizePicksAPI")
        self.base_url = "https://api.prizepicks.com"
        self.device_id = str(uuid.uuid4())
        logger.debug(f"Generated device ID: {self.device_id}")
        
        # Standard headers required for the API
        self.headers = {
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Referer': 'https://app.prizepicks.com/',
            'X-Device-ID': self.device_id,
            'sec-ch-ua-platform': '"macOS"'
        }
        logger.debug(f"Initialized headers: {json.dumps(self.headers, indent=2)}")

    def get_projections(self, league: str = 'NBA', per_page: int = 250, date_str: Optional[str] = None) -> Dict:
        """
        Get projections for a specific league and date
        
        Args:
            league (str): League name (default: 'NBA')
            per_page (int): Number of projections to return (default: 250)
            date_str (str, optional): Date in YYYY-MM-DD format
            
        Returns:
            Dict: JSON response containing projections
        """
        logger.info(f"Fetching projections for league: {league}, date: {date_str}")
        
        league_id = self.LEAGUE_IDS.get(league.upper())
        if not league_id:
            logger.error(f"Unknown league: {league}")
            raise ValueError(f"Unknown league: {league}")
            
        params = {
            'league_id': league_id,
            'per_page': per_page,
            'single_stat': 'true',
            'game_mode': 'pickem'
        }
        
        # Add date filter if provided
        if date_str:
            params['date'] = date_str
            
        logger.debug(f"Request parameters: {json.dumps(params, indent=2)}")
        
        try:
            logger.debug("Establishing HTTP connection")
            conn = http.client.HTTPSConnection("api.prizepicks.com")
            
            # Build query string
            query = '&'.join(f"{k}={v}" for k, v in params.items())
            full_url = f"/projections?{query}"
            logger.debug(f"Full request URL: {self.base_url}{full_url}")
            
            logger.debug("Sending request")
            conn.request("GET", full_url, headers=self.headers)
            
            logger.debug("Getting response")
            response = conn.getresponse()
            logger.info(f"Response status: {response.status} {response.reason}")
            logger.debug(f"Response headers: {dict(response.getheaders())}")
            
            data = response.read()
            decoded_data = data.decode("utf-8")
            
            # Log first 500 characters of response for debugging
            logger.debug(f"Response preview: {decoded_data[:500]}...")
            
            try:
                # Try to parse as JSON to verify response format
                json_data = json.loads(decoded_data)
                logger.info("Successfully parsed response as JSON")
                return json_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response as JSON: {str(e)}")
                logger.debug(f"Raw response: {decoded_data}")
                raise
            
        except Exception as e:
            logger.error(f"Failed to fetch projections: {str(e)}", exc_info=True)
            raise Exception(f"Failed to fetch projections: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
                logger.debug("Closed connection")

    def parse_projections(self, data: Dict, date_str: Optional[str] = None) -> List[Dict]:
        """
        Parse the raw projections data into a more usable format, focusing on goblin games
        
        Args:
            data (Dict): Raw API response data
            date_str (str, optional): Date in YYYY-MM-DD format to filter by
            
        Returns:
            List[Dict]: List of parsed goblin game projections with player and team info
        """
        logger.info(f"Parsing projections data for goblin games, date: {date_str}")
        try:
            if not data.get('data'):
                logger.warning("No projection data found")
                return []

            # Create lookup dictionaries for included data
            included = data.get('included', [])
            players = {
                item['id']: item['attributes'] 
                for item in included 
                if item['type'] == 'new_player'
            }
            teams = {
                item['id']: item['attributes']
                for item in included
                if item['type'] == 'team'
            }
            
            goblin_props = []
            
            for projection in data['data']:
                attrs = projection.get('attributes', {})
                
                # Filter for goblin games
                if attrs.get('odds_type') != 'goblin':
                    continue
                
                # Filter by date if provided
                if date_str:
                    start_time = attrs.get('start_time')
                    if not start_time:
                        continue
                    
                    # Convert start_time to date string for comparison
                    try:
                        prop_date = datetime.fromisoformat(start_time.replace('Z', '+00:00')).date()
                        filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        if prop_date != filter_date:
                            continue
                    except ValueError as e:
                        logger.warning(f"Failed to parse date for projection {projection.get('id')}: {e}")
                        continue
                
                # Get player ID from relationships
                player_id = (projection.get('relationships', {})
                           .get('new_player', {})
                           .get('data', {})
                           .get('id'))
                
                if not player_id:
                    logger.warning(f"No player ID found for projection {projection.get('id')}")
                    continue
                
                # Get player info
                player_info = players.get(player_id, {})
                
                # Build prop dictionary
                prop = {
                    'projection_id': projection.get('id'),
                    'line_score': attrs.get('line_score'),
                    'stat_type': attrs.get('stat_type'),
                    'description': attrs.get('description'),
                    'start_time': attrs.get('start_time'),
                    'end_time': attrs.get('end_time'),
                    'player': {
                        'id': player_id,
                        'name': player_info.get('name'),
                        'display_name': player_info.get('display_name'),
                        'position': player_info.get('position'),
                        'team': player_info.get('team'),
                        'team_name': player_info.get('team_name')
                    }
                }
                
                goblin_props.append(prop)
            
            logger.info(f"Found {len(goblin_props)} goblin game projections for date: {date_str}")
            return goblin_props
            
        except Exception as e:
            logger.error(f"Failed to parse projections: {str(e)}", exc_info=True)
            raise

    def get_current_goblin_props(self, date_str: Optional[str] = None) -> List[Dict]:
        """
        Get all current NBA goblin props, optionally filtered by date
        
        Args:
            date_str (str, optional): Date in YYYY-MM-DD format to filter props by
            
        Returns:
            List[Dict]: List of current goblin props
        """
        logger.info(f"Fetching current goblin props for date: {date_str}")
        try:
            raw_data = self.get_projections(league='NBA', date_str=date_str)
            return self.parse_projections(raw_data, date_str=date_str)
        except Exception as e:
            logger.error(f"Failed to get goblin props: {str(e)}", exc_info=True)
            raise 