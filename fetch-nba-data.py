import os
from nba_api_wrapper import NBAApiWrapper


nba_api = NBAApiWrapper()

# fetch all stats for the last 5 seasons
for season in range(2019, 2024):
    filename = f"player_stats_{season}.json"
    if os.path.exists(filename):
        print(f"Skipping {filename} because it already exists")
        continue
    nba_api.save_all_player_stats(season=season, filename=filename)