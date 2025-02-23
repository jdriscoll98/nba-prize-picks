import json
from typing import Dict, List, Callable, Optional
import logging
import sys
from statistics import mean, stdev
from sklearn.linear_model import LogisticRegression
import numpy as np
from scipy import stats

# Configure logging
def setup_logging(debug_mode=False):
    log_level = logging.DEBUG if debug_mode else logging.INFO
    console_level = logging.DEBUG if debug_mode else logging.WARNING
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('analyzer_debug.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set console output to be less verbose
    logging.getLogger().handlers[1].setLevel(console_level)

logger = logging.getLogger(__name__)

# Initialize with default (non-debug) logging
setup_logging()

# Add function to enable debug mode
def enable_debug_logging():
    setup_logging(debug_mode=True)

class PropAnalyzer:
    """Analyzes player props against historical stats"""
    
    STAT_TYPE_MAPPING = {
        'Points': 'points',
        'Rebounds': 'totReb',
        'Assists': 'assists',
        'Blocks': 'blocks',
        'Steals': 'steals',
        'Turnovers': 'turnovers',
        '3-PT Made': 'tpm',
        'Fantasy Score': None,  # Needs special calculation
    }
    
    def __init__(self, stats_file: str = "nba_stats_2024.json", props_file: str = "prize_picks_current_goblin_props.json"):
        """Initialize the analyzer"""
        logger.info(f"Initializing PropAnalyzer with stats_file={stats_file}, props_file={props_file}")
        self.stats_data = self._load_json(stats_file)
        logger.info(f"Loaded {len(self.stats_data)} game stats")
        self.props_data = self._load_json(props_file)
        logger.info(f"Loaded {len(self.props_data)} props")
        
        # Log available player names from both datasets
        stats_players = set(
            f"{game['player']['firstname']} {game['player']['lastname']}"
            for game in self.stats_data
            if 'player' in game and 'firstname' in game['player'] and 'lastname' in game['player']
        )
        props_players = set(prop.get('player', {}).get('name') for prop in self.props_data)
        logger.debug(f"Players in stats: {stats_players}")
        logger.debug(f"Players in props: {props_players}")
        
        # Log stat types from props
        prop_types = set(prop.get('stat_type') for prop in self.props_data)
        logger.debug(f"Prop types found: {prop_types}")
        logger.debug(f"Available stat mappings: {self.STAT_TYPE_MAPPING.keys()}")

    def _load_json(self, filepath: str) -> Dict:
        """Load JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {str(e)}")
            raise

    def get_probability_distribution(
        self, 
        player_name: str, 
        stat_type: str,
        num_recent_games: int = 20
    ) -> Optional[Callable[[float], float]]:
        """
        Fit a probability distribution to player's historical performance.
        Returns a function that calculates P(stat > x) for any x.
        """
        try:
            # Get player's games
            player_stats = [
                game for game in self.stats_data
                if (game.get('player', {}).get('firstname', '') + ' ' + 
                    game.get('player', {}).get('lastname', '')).strip() == player_name
            ]

            if len(player_stats) < 10:  # Minimum games needed for meaningful distribution
                logger.warning(f"Insufficient games for {player_name}: {len(player_stats)} < 10")
                return None

            stat_key = self.STAT_TYPE_MAPPING.get(stat_type)
            if not stat_key:
                logger.error(f"Unknown stat type: {stat_type}")
                return None

            # Get stat values and minutes
            values = []
            minutes = []
            for game in player_stats:
                try:
                    value = float(game.get(stat_key, 0))
                    mins = float(game.get('min', 0))
                    if mins > 0:  # Only include games with playing time
                        values.append(value)
                        minutes.append(mins)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error processing game stat: {e}")
                    continue

            if not values:
                return None

            # Calculate weights based on recency and minutes
            weights = []
            avg_minutes = mean(minutes)
            for i, (value, mins) in enumerate(zip(values, minutes)):
                # Recency weight: exponential decay
                recency_weight = np.exp(-i / num_recent_games) if i < num_recent_games else 0.1
                # Minutes weight: higher weight for games closer to average minutes
                minutes_weight = 1 - abs(mins - avg_minutes) / (2 * avg_minutes)
                weights.append(recency_weight * minutes_weight)

            # Normalize weights
            weights = np.array(weights)
            weights = weights / weights.sum()

            # Fit kernel density estimation with weighted samples
            kde = stats.gaussian_kde(values, weights=weights, bw_method='silverman')

            # Create probability function
            def prob_over_threshold(x: float) -> float:
                """Calculate P(stat > x) using fitted distribution"""
                try:
                    # Integrate from x to a reasonable upper bound
                    upper_bound = max(values) * 1.5
                    prob = kde.integrate_box_1d(x, upper_bound)
                    return min(max(prob, 0), 1)  # Ensure probability is between 0 and 1
                except Exception as e:
                    logger.error(f"Error calculating probability: {e}")
                    return 0.0

            return prob_over_threshold

        except Exception as e:
            logger.error(f"Error creating probability distribution: {e}")
            return None

    def get_probabilities_table(
        self, 
        player_name: str, 
        stat_type: str, 
        num_recent_games: int = 20,
        step: float = 0.5  # Increment between thresholds
    ) -> List[Dict[str, float]]:
        """
        Generate table of probabilities at different thresholds
        """
        prob_func = self.get_probability_distribution(player_name, stat_type, num_recent_games)
        if not prob_func:
            return []

        try:
            # Get player's stats for determining range
            player_stats = [
                game for game in self.stats_data
                if (game.get('player', {}).get('firstname', '') + ' ' + 
                    game.get('player', {}).get('lastname', '')).strip() == player_name
            ]

            stat_key = self.STAT_TYPE_MAPPING.get(stat_type)
            values = [float(game.get(stat_key, 0)) for game in player_stats if game.get(stat_key)]

            if not values:
                return []

            # Generate thresholds from 0 to max historical value
            max_val = max(values)
            thresholds = np.arange(0, max_val + step, step)

            # Calculate probabilities for each threshold
            probabilities = []
            for threshold in thresholds:
                prob = prob_func(threshold)
                probabilities.append({
                    "threshold": round(threshold, 1),
                    "probability": round(prob, 3)
                })

            return probabilities

        except Exception as e:
            logger.error(f"Error generating probabilities table: {e}")
            return []

    def analyze_player_stats(self, player_stats: List[Dict], prop_type: str, line_score: float) -> Dict:
        """Analyze a player's stats against a prop line"""
        stat_key = self.STAT_TYPE_MAPPING.get(prop_type)
        
        values = []
        minutes = []
        differences_when_above = []
        
        # Get recent games (last 10)
        recent_games = player_stats[-10:]
        recent_values = []
        recent_hits = 0
        
        for i, game in enumerate(player_stats):
            try:
                if not game.get('min'):
                    continue
                    
                minutes.append(float(game['min']))
                value = float(game.get(stat_key, 0))
                values.append(value)
                
                if value > line_score:
                    differences_when_above.append(value - line_score)
                
            except Exception as e:
                logger.error(f"Error processing game {i}: {str(e)}")
                continue
        
        # Process recent games
        for game in recent_games:
            try:
                value = float(game.get(stat_key, 0))
                recent_values.append(value)
                if value > line_score:
                    recent_hits += 1
            except:
                continue
            
        if not values:
            return {}
            
        result = {
            'games_played': len(values),
            'times_above_line': len(differences_when_above),
            'average_value': mean(values),
            'average_minutes': mean(minutes) if minutes else 0,
            'minutes_stdev': stdev(minutes) if len(minutes) > 1 else 0,
            'average_difference': mean(differences_when_above) if differences_when_above else 0,
            'stat_type': prop_type,
            'line_score': line_score,
            'recent_average': mean(recent_values) if recent_values else 0,
            'recent_hit_rate': recent_hits / len(recent_games) if recent_games else 0,
            'recent_values': recent_values[-10:]  # Last 10 games
        }
        
        # Add probability distribution analysis
        try:
            player_name = (
                player_stats[0].get('player', {}).get('firstname', '') + ' ' +
                player_stats[0].get('player', {}).get('lastname', '')
            ).strip()
            
            prob_func = self.get_probability_distribution(player_name, prop_type)
            if prob_func:
                result['probability_over_line'] = prob_func(line_score)
                
                # Add key thresholds
                result['probability_distribution'] = {
                    'over_minus_5': prob_func(line_score - 5),
                    'over_minus_2': prob_func(line_score - 2),
                    'over_line': prob_func(line_score),
                    'over_plus_2': prob_func(line_score + 2),
                    'over_plus_5': prob_func(line_score + 5)
                }
        except Exception as e:
            logger.debug(f"Error adding probability distribution: {e}")

        return result

    def calculate_prop_score(self, analysis: Dict) -> float:
        """Calculate a score for how good a prop bet is"""
        if not analysis:
            return 0.0
            
        # Factors to consider:
        # 1. How often they hit (percentage)
        # 2. Average difference when they hit
        # 3. Consistency of playing time (lower stdev is better)
        # 4. Sample size (more games is better)
        
        hit_rate = analysis['times_above_line'] / analysis['games_played']
        minutes_consistency = 1 / (1 + analysis['minutes_stdev'])  # Normalize to 0-1
        sample_size_factor = min(analysis['games_played'] / 20, 1)  # Cap at 20 games
        
        score = (
            hit_rate * 0.4 +  # 40% weight on hit rate
            (analysis['average_difference'] / 10) * 0.3 +  # 30% weight on average difference
            minutes_consistency * 0.2 +  # 20% weight on minutes consistency
            sample_size_factor * 0.1  # 10% weight on sample size
        )
        
        return score

    def find_best_props(self, min_games: int = 5) -> List[Dict]:
        """Find and rank the best prop bets"""
        logger.info(f"Finding best props with minimum {min_games} games")
        analyzed_props = []
        
        for prop in self.props_data:
            player_name = prop['player']['name']
            stat_type = prop.get('stat_type')
            line_score = prop.get('line_score')
            
            # logger.debug(f"\nAnalyzing prop: {player_name} - {stat_type} {line_score}")
            
            player_stats = [
                game for game in self.stats_data
                if (game.get('player', {}).get('firstname', '') + ' ' + 
                    game.get('player', {}).get('lastname', '')).strip() == player_name
            ]
            
            # logger.debug(f"Found {len(player_stats)} games for {player_name}")
            
            if len(player_stats) < min_games:
                # logger.debug(f"Skipping {player_name} - insufficient games ({len(player_stats)} < {min_games})")
                continue
            
            if stat_type not in self.STAT_TYPE_MAPPING:
                # logger.warning(f"Unknown stat type: {stat_type}")
                continue
                
            try:
                analysis = self.analyze_player_stats(
                    player_stats,
                    stat_type,
                    float(line_score)
                )
                
                if analysis:
                    score = self.calculate_prop_score(analysis)
                    # logger.debug(f"Analysis for {player_name}:")
                    # logger.debug(f"- Games: {analysis['games_played']}")
                    # logger.debug(f"- Times above line: {analysis['times_above_line']}")
                    # logger.debug(f"- Average value: {analysis['average_value']:.2f}")
                    # logger.debug(f"- Score: {score:.3f}")
                    
                    analyzed_props.append({
                        'prop': prop,
                        'analysis': analysis,
                        'score': score
                    })
                else:
                    logger.warning(f"No valid analysis for {player_name}")
                    
            except Exception as e:
                logger.error(f"Error analyzing {player_name}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Successfully analyzed {len(analyzed_props)} props")
        return sorted(analyzed_props, key=lambda x: x['score'], reverse=True)