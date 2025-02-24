import argparse
from nba_api_wrapper import NBAApiWrapper
from prize_picks_scraper import PrizePicksAPI
from prop_analyzer import PropAnalyzer, enable_debug_logging
import json
from typing import Dict, List

def analyze_all_props(analyzer: PropAnalyzer, props: List[Dict]) -> List[Dict]:
    """Analyze all props using probability distributions"""
    analyzed_props = []
    
    for prop in props:
        player_name = prop['player']['name']
        stat_type = prop.get('stat_type')
        line_score = float(prop.get('line_score', 0))
        
        # Get probability table
        prob_table = analyzer.get_probabilities_table(player_name, stat_type)
        if not prob_table:
            continue
            
        # Get probability function for additional thresholds
        prob_func = analyzer.get_probability_distribution(player_name, stat_type)
        if not prob_func:
            continue
            
        # Get basic analysis
        player_stats = [
            game for game in analyzer.stats_data
            if (game.get('player', {}).get('firstname', '') + ' ' + 
                game.get('player', {}).get('lastname', '')).strip() == player_name
        ]
        
        analysis = analyzer.analyze_player_stats(player_stats, stat_type, line_score)
        if not analysis:
            continue
            
        # Calculate key probabilities
        prob_over_line = prob_func(line_score)
        
        analyzed_props.append({
            'prop': prop,
            'analysis': analysis,
            'probability_table': prob_table,
            'key_probabilities': {
                'over_line': round(prob_over_line, 3),
            }
        })
    
    # Sort by probability of hitting
    return sorted(analyzed_props, key=lambda x: x['key_probabilities']['over_line'], reverse=True)

def main():
    parser = argparse.ArgumentParser(description='Analyze NBA props')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--refresh-stats', type=bool, default=False, help='Refresh stats')
    args = parser.parse_args()
    
    if args.debug:
        enable_debug_logging()
    
    if args.refresh_stats:
        nba_api = NBAApiWrapper()
        nba_api.save_all_player_stats()
        nba_api.get_games(season=2024)

    prize_picks = PrizePicksAPI()
    props = prize_picks.get_current_goblin_props()
    
    # Save current props
    with open('prize_picks_current_goblin_props.json', 'w') as f:
        json.dump(props, f)
    
    # Analyze all props
    analyzer = PropAnalyzer()
    analyzed_props = analyze_all_props(analyzer, props)
    
    # Print results
    print("\nProp Analysis Results:")
    print("=====================")
    
    for prop in analyzed_props:
        player = prop['prop']['player']['name']
        stat = prop['prop']['stat_type']
        line = prop['prop']['line_score']
        prob = prop['key_probabilities']['over_line']
        recent_rate = prop['analysis']['recent_hit_rate']
        season_rate = prop['analysis']['times_above_line'] / prop['analysis']['games_played']
        
        print(f"\n{player} - {stat} {line}")
        print(f"Probability over line: {prob:.1%}")
        print(f"Recent hit rate: {recent_rate:.1%}")
        print(f"Season hit rate: {season_rate:.1%}")
    
    # Save detailed analysis to file
    with open('prop_analysis.json', 'w') as f:
        json.dump(analyzed_props, f, indent=2)

if __name__ == "__main__":
    main()