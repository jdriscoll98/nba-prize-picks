import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, mean_squared_error, r2_score

REBOUND_TARGET = 5.5
PLAYER_ID = 972
data = []
for season in range(2022, 2025):
    filename = f"player_stats_{season}.json"
    with open(filename, "r") as f:
        season_data = json.load(f)
    data.extend(season_data)
df = pd.json_normalize(data)

# print the first row's id
# load X from nba_stats_2024.json

df = df[df["min"].notna() & (df["min"] != "--") & (df["min"] != "-")]
# then split the string into minutes and seconds
df["min"] = df["min"].str.split(":").str[0].astype(int)

df["historical_avg_mins"] = df.groupby("player.id")["min"].transform(
    lambda x: x.expanding().mean().shift()
)
df.fillna({"historical_avg_mins": 0}, inplace=True)


df['moving_avg_mins'] = df.groupby('player.id')['min'].transform(
    lambda x: x.shift().rolling(window=10, min_periods=1).mean()
)
df.fillna({'moving_avg_mins': 0}, inplace=True)


# Compute the historical average rebounds per game (excluding the current game)
df["historical_avg_reb"] = df.groupby("player.id")["totReb"].transform(
    lambda x: x.expanding().mean().shift()
)
df.fillna({"historical_avg_reb": 0}, inplace=True)

# Alternatively, compute a moving average over the last 3 games (again shifting so the current game isn't included)
df["moving_avg_reb"] = df.groupby("player.id")["totReb"].transform(
    lambda x: x.shift().rolling(window=10, min_periods=1).mean()
)
df.fillna({"moving_avg_reb": 0}, inplace=True)

features = ["historical_avg_mins", 'moving_avg_mins', "historical_avg_reb", "moving_avg_reb"]
X = df[features]


y = df["totReb"] > REBOUND_TARGET

# Assume X is your feature matrix and y is your binary target variable.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# # Initialize and train the model.
model = LogisticRegression(solver="lbfgs", max_iter=1000)
# model = LinearRegression()
model.fit(X_train, y_train)

# print accuracy, confusion matrix, and feature importance
accuracy = accuracy_score(y_test, model.predict(X_test))
cm = confusion_matrix(y_test, model.predict(X_test))
featImportance = pd.DataFrame({"feature": features, "importance": model.coef_[0]})
print("Accuracy:", accuracy)
print("Confusion Matrix:\n", cm)
print("Feature Importance:", featImportance)

# # Make predictions.
# Filter the DataFrame for the specific player.
# If the player has multiple records (games), you can select the most recent one:
player_record = df[df["player.id"] == PLAYER_ID].iloc[-1]

# Extract the features for that specific record
player_features = player_record[features].to_numpy().astype(float)
probabilities = model.predict_proba([player_features])[0]

print("Probability of not exceeding", REBOUND_TARGET, "rebounds:", probabilities[0])
print("Probability of exceeding", REBOUND_TARGET, "rebounds:", probabilities[1])