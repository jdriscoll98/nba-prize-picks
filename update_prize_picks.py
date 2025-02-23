
from prize_picks_scraper import PrizePicksAPI
import json

prize_picks = PrizePicksAPI()
props = prize_picks.get_current_goblin_props()
    
# Save current props
with open('prize_picks_current_goblin_props.json', 'w') as f:
    json.dump(props, f)