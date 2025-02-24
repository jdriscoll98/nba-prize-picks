import json
import os
from nba_api_wrapper import NBAApiWrapper


nba_api = NBAApiWrapper()

# fetch all stats for the last 3 seasons
for season in range(2022, 2025):
    filename = f"player_stats_{season}.json"
    # if os.path.exists(filename):
    #     print(f"Skipping {filename} because it already exists")
    #     continue
    nba_api.save_all_player_stats(season=season, filename=filename)

# teams = nba_api.get_all_teams()
# with open("teams.json", "w") as f:
#     json.dump(teams, f)
