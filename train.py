import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier

os.makedirs('models', exist_ok=True)
df = pd.read_csv('data/raw/all_leagues.csv')
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.sort_values('Date')
df = df.dropna(subset=['FTHG', 'FTAG', 'FTR'])

# Make sure HC/AC exist even if UCL/UEL have no corners
if 'HC' not in df.columns:
    df['HC'] = None
if 'AC' not in df.columns:
    df['AC'] = None

has_corners = df['HC'].notna().sum() > 0
print(f"Has corners data: {has_corners} - Games with corners: {df['HC'].notna().sum()} / {len(df)}")

def get_stats(team, league, df_all, before_date):
    games = df_all[((df_all['HomeTeam'] == team) | (df_all['AwayTeam'] == team))]
    if 'League' in df_all.columns:
        games = games[games['League'] == league]
    games = games[games['Date'] < before_date].tail(5)
    if len(games) == 0:
        return 1.2, 1.2, 0.33, 1.0, 0.5, 5.0, 5.0
    scored, conceded, corners_for, corners_against = [], [], [], []
    points, wins = 0, 0
    for _, r in games.iterrows():
        is_home = r['HomeTeam'] == team
        if is_home:
            scored.append(r['FTHG']); conceded.append(r['FTAG'])
            if pd.notna(r['HC']) and pd.notna(r['AC']):
                corners_for.append(r['HC']); corners_against.append(r['AC'])
            if r['FTR'] == 'H': points+=3; wins+=1
            elif r['FTR'] == 'D': points+=1
        else:
            scored.append(r['FTAG']); conceded.append(r['FTHG'])
            if pd.notna(r['HC']) and pd.notna(r['AC']):
                corners_for.append(r['AC']); corners_against.append(r['HC'])
            if r['FTR'] == 'A': points+=3; wins+=1
            elif r['FTR'] == 'D': points+=1
    avg_corners_for = sum(corners_for)/len(corners_for) if corners_for else 5.0
    avg_corners_against = sum(corners_against)/len(corners_against) if corners_against else 5.0
    return sum(scored)/len(scored), sum(conceded)/len(conceded), wins/len(games), points/len(games), points/(len(games)*3), avg_corners_for, avg_corners_against

rows = []
for _, row in df.iterrows():
    league = row['League'] if 'League' in df.columns else 'Unknown'
    h = get_stats(row['HomeTeam'], league, df, row['Date'])
    a = get_stats(row['AwayTeam'], league, df, row['Date'])
    total_goals = row['FTHG'] + row['FTAG']
    has_this_game_corners = pd.notna(row['HC']) and pd.notna(row['AC'])
    total_corners = (row['HC'] + row['AC']) if has_this_game_corners else 0
    rows.append({
        'home_avg_goals_scored': h[0], 'home_avg_goals_conceded': h[1], 'home_win_rate': h[2], 'home_points_per_game': h[3], 'home_form': h[4],
        'home_avg_corners': h[5], 'away_avg_corners': a[5],
        'home_goals_diff': h[0]-h[1],
        'away_avg_goals_scored': a[0], 'away_avg_goals_conceded': a[1], 'away_win_rate': a[2], 'away_points_per_game': a[3], 'away_form': a[4],
        'away_goals_diff': a[0]-a[1],
        'goals_scored_diff': h[0]-a[0], 'goals_conceded_diff': h[1]-a[1], 'form_diff': h[4]-a[4], 'points_diff': h[3]-a[3],
        'corners_diff': h[5]-a[5], 'total_avg_corners': h[5]+a[5],
        'result': row['FTR'],
        'over_25_goals': 1 if total_goals > 2.5 else 0,
        'over_95_corners': 1 if total_corners > 9.5 else 0,
        'has_corners': 1 if has_this_game_corners else 0,
    })

data = pd.DataFrame(rows)
feature_columns = [c for c in data.columns if c not in ['result','over_25_goals','over_95_corners','has_corners']]
X = data[feature_columns]

# 1. Result
m1 = RandomForestClassifier(n_estimators=100, random_state=42)
m1.fit(X, data['result'])
joblib.dump(m1, 'models/football_model.pkl')
print(f"Result model trained on {len(data)} games")

# 2. Over/Under Goals
m2 = RandomForestClassifier(n_estimators=100, random_state=42)
m2.fit(X, data['over_25_goals'])
joblib.dump(m2, 'models/over_under_model.pkl')
print(f"Over 2.5 Goals model trained")

# 3. Corners - ONLY on games that have corners
if has_corners:
    corners_data = data[data['has_corners'] == 1]
    print(f"Training corners model on {len(corners_data)} games with corners only")
    m3 = RandomForestClassifier(n_estimators=100, random_state=42)
    m3.fit(corners_data[feature_columns], corners_data['over_95_corners'])
    joblib.dump(m3, 'models/corners_model.pkl')
    print(f"Corners model trained")
else:
    print("Skipped corners model - no HC/AC in CSV")

joblib.dump(feature_columns, 'models/feature_columns.pkl')
print("All saved!")