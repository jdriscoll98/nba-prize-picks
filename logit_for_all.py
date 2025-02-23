import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_squared_error,
    r2_score,
)

# load props from prize picks
with open("prize_picks_current_goblin_props.json", "r") as f:
    props = json.load(f)

# Stat Types:
# {'Rebs+Asts', 'Pts+Rebs+Asts', 'Assists', 'Blocked Shots', 'Rebounds', 'Points', '3-PT Made', 'Pts+Asts', 'Turnovers', 'Steals', 'Pts+Rebs'}

# Available Features:
# ['points', 'pos', 'min', 'fgm', 'fga', 'fgp', 'ftm', 'fta', 'ftp', 'tpm',
#        'tpa', 'tpp', 'offReb', 'defReb', 'totReb', 'assists', 'pFouls',
#        'steals', 'turnovers', 'blocks', 'plusMinus', 'comment', 'player.id',
#        'player.firstname', 'player.lastname', 'team.id', 'team.name',
#        'team.nickname', 'team.code', 'team.logo', 'game.id']
STAT_MAP = {
    # "Rebs+Asts": "totReb + assists",
    # "Pts+Rebs+Asts": "pts + totReb + assists",
    "Assists": "assists",
    "Blocked Shots": "blocks",
    "Rebounds": "totReb",
    # "Points": "fgm + tpm",
    "3-PT Made": "tpm",
    # "Pts+Asts": "pts + assists",
    # "Turnovers": "turnovers",
    "Steals": "steals",
    # "Pts+Rebs": "pts + totReb",
}
data = []
for season in range(2019, 2024):
    filename = f"player_stats_{season}.json"
    with open(filename, "r") as f:
        season_data = json.load(f)
    data.extend(season_data)
df = pd.json_normalize(data)


df = df[df["min"].notna() & (df["min"] != "--") & (df["min"] != "-")]
df["min"] = df["min"].str.split(":").str[0].astype(int)
df["historical_avg_mins"] = df.groupby("player.id")["min"].transform(
    lambda x: x.expanding().mean().shift()
)
df.fillna({"historical_avg_mins": 0}, inplace=True)
df["moving_avg_mins"] = df.groupby("player.id")["min"].transform(
    lambda x: x.shift().rolling(window=10, min_periods=1).mean()
)
df.fillna({"moving_avg_mins": 0}, inplace=True)
df['name'] = df['player.firstname'] + ' ' + df['player.lastname']

predictions = []
for prop in props:
    # get the stat_type from the prop
    stat_type = prop.get("stat_type")
    # get the player_name from the prop
    player_name = prop.get("player", {}).get("name")
    # find the player_id from the player_name
    players = df[df["name"] == player_name]["player.id"].values
    if len(players) == 0:
        print(f"Player {player_name} not found")
        continue
    player_id = players[0]
    # get the value from the prop
    value = prop.get("line_score")
    print(player_id, player_name, stat_type, value)

    # get the stat_type from the STAT_MAP
    stat = STAT_MAP.get(stat_type, None)
    if stat is None:
        print(f"Stat type {stat_type} not found")
        continue
    
    # Compute the historical average stat per game (excluding the current game)
    df["historical_avg_stat"] = df.groupby("player.id")[stat].transform(
        lambda x: x.expanding().mean().shift()
    )
    df.fillna({"historical_avg_stat": 0}, inplace=True)

    # Alternatively, compute a moving average over the last 3 games (again shifting so the current game isn't included)
    df["moving_avg_stat"] = df.groupby("player.id")[stat].transform(
        lambda x: x.shift().rolling(window=10, min_periods=1).mean()
    )
    df.fillna({"moving_avg_stat": 0}, inplace=True)

    features = ["historical_avg_mins", 'moving_avg_mins', "historical_avg_stat", "moving_avg_stat"]
    X = df[features]


    y = df[stat] > value

    # # Assume X is your feature matrix and y is your binary target variable.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # # # Initialize and train the model.
    model = LogisticRegression(solver="lbfgs", max_iter=1000)
    model.fit(X_train, y_train)

    # print accuracy, confusion matrix, and feature importance
    accuracy = accuracy_score(y_test, model.predict(X_test))
    cm = confusion_matrix(y_test, model.predict(X_test))
    featImportance = pd.DataFrame({"feature": features, "importance": model.coef_[0]})

    # # Make predictions.
    # Filter the DataFrame for the specific player.
    # If the player has multiple records (games), you can select the most recent one:
    player_record = df[df["player.id"] == player_id].iloc[-1]

    # Extract the features for that specific record
    player_features = player_record[features].to_numpy().astype(float)
    probabilities = model.predict_proba([player_features])[0]

    # print("Probability of not exceeding", value, stat_type, ":", probabilities[0])
    # print("Probability of exceeding", value, stat_type, ":", probabilities[1])
    predictions.append({
        "player_name": player_name,
        "stat_type": stat_type,
        "value": value,
        "probability": probabilities[1],
        "model_info": {
            "accuracy": accuracy,
            "confusion_matrix": cm.tolist(),
            "feature_importance": featImportance.to_dict(orient="records")
        }
    })

# save the predictions to a json file
with open("predictions.json", "w") as f:
    json.dump(predictions, f)
