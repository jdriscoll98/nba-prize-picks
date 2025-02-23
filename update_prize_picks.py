from datetime import datetime, timedelta
from prize_picks_scraper import PrizePicksAPI
import json

# read the current prize_picks_current_goblin_props.json file
with open('prize_picks_current_goblin_props.json', 'r') as f:
    current_props = json.load(f)

# dump the current props to an archive file
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
with open(f'prize_picks_current_goblin_props_{yesterday}.json', 'w') as f:
    json.dump(current_props, f) 

prize_picks = PrizePicksAPI()
props = prize_picks.get_current_goblin_props()
    
# Save current props
with open('prize_picks_current_goblin_props.json', 'w') as f:
    json.dump(props, f)