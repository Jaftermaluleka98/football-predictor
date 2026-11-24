import joblib
import pandas as pd

# Load model with joblib - NOT pickle
model = joblib.load('models/football_model.pkl')
feature_columns = joblib.load('models/feature_columns.pkl')

print("Model loaded!")
print("Features needed:", feature_columns)

df = pd.read_csv('data/raw/all_leagues.csv')
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.sort_values('Date')

def get_team_stats(team, league):
    games = df[((df['HomeTeam'] == team) | (df['AwayTeam'] == team))]
    if 'League' in df.columns:
        games = games[games['League'] == league]
    games = games.tail(5)
    if len(games) == 0:
        return {'avg_goals_scored': 1.2, 'avg_goals_conceded': 1.2, 'win_rate': 0.33, 'points_per_game': 1.0, 'form': 0.5}
    scored = []
    conceded = []
    points = 0
    wins = 0
    for _, row in games.iterrows():
        if row['HomeTeam'] == team:
            scored.append(row['FTHG'])
            conceded.append(row['FTAG'])
            if row['FTR'] == 'H':
                points += 3
                wins += 1
            elif row['FTR'] == 'D':
                points += 1
        else:
            scored.append(row['FTAG'])
            conceded.append(row['FTHG'])
            if row['FTR'] == 'A':
                points += 3
                wins += 1
            elif row['FTR'] == 'D':
                points += 1
    return {'avg_goals_scored': sum(scored)/len(scored), 'avg_goals_conceded': sum(conceded)/len(conceded), 'win_rate': wins/len(games), 'points_per_game': points/len(games), 'form': points/(len(games)*3)}

def predict_match(home_team, away_team, league):
    home = get_team_stats(home_team, league)
    away = get_team_stats(away_team, league)
    features = {}
    features['home_avg_goals_scored'] = home['avg_goals_scored']
    features['home_avg_goals_conceded'] = home['avg_goals_conceded']
    features['home_win_rate'] = home['win_rate']
    features['home_points_per_game'] = home['points_per_game']
    features['home_form'] = home['form']
    features['home_goals_diff'] = home['avg_goals_scored'] - home['avg_goals_conceded']
    features['away_avg_goals_scored'] = away['avg_goals_scored']
    features['away_avg_goals_conceded'] = away['avg_goals_conceded']
    features['away_win_rate'] = away['win_rate']
    features['away_points_per_game'] = away['points_per_game']
    features['away_form'] = away['form']
    features['away_goals_diff'] = away['avg_goals_scored'] - away['avg_goals_conceded']
    features['goals_scored_diff'] = home['avg_goals_scored'] - away['avg_goals_scored']
    features['goals_conceded_diff'] = home['avg_goals_conceded'] - away['avg_goals_conceded']
    features['form_diff'] = home['form'] - away['form']
    features['points_diff'] = home['points_per_game'] - away['points_per_game']
    row = []
    for col in feature_columns:
        if col in features:
            row.append(features[col])
        else:
            row.append(0)
    X = pd.DataFrame([row], columns=feature_columns)
    prediction = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    print(f"\n--- {home_team} vs {away_team} ({league}) ---")
    print(f"Home Form: {home['form']:.2f} | Away Form: {away['form']:.2f}")
    print(f"Home Goals: {home['avg_goals_scored']:.2f} | Away Goals: {away['avg_goals_scored']:.2f}")
    print(f"\nPrediction: {prediction}")
    classes = list(model.classes_)
    for i, cls in enumerate(classes):
        print(f"{cls}: {proba[i]*100:.1f}%")
    return prediction, proba

if __name__ == "__main__":
    print("\nAvailable leagues:")
    if 'League' in df.columns:
        print(df['League'].unique())
    home = input("\nEnter Home Team: ").strip()
    away = input("Enter Away Team: ").strip()
    league = input("Enter League: ").strip()
    predict_match(home, away, league)