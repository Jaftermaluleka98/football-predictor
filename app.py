import streamlit as st
import joblib
import pandas as pd

st.set_page_config(page_title="Football Predictor", page_icon="⚽")
st.title("⚽ Football Predictor")
st.write("Pick a match and see the prediction")

@st.cache_resource
def load_model():
    model = joblib.load('models/football_model.pkl')
    feature_columns = joblib.load('models/feature_columns.pkl')
    return model, feature_columns

model, feature_columns = load_model()

@st.cache_data
def load_data():
    df = pd.read_csv('data/raw/all_leagues.csv')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values('Date')
    return df

df = load_data()

def get_team_stats(team, league):
    games = df[((df['HomeTeam'] == team) | (df['AwayTeam'] == team))]
    if 'League' in df.columns:
        games = games[games['League'] == league]
    games = games.tail(5)
    if len(games) == 0:
        return {'avg_goals_scored': 1.2, 'avg_goals_conceded': 1.2, 'win_rate': 0.33, 'points_per_game': 1.0, 'form': 0.5, 'avg_corners': 5.0}
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
    return {'avg_goals_scored': sum(scored)/len(scored), 'avg_goals_conceded': sum(conceded)/len(conceded), 'win_rate': wins/len(games), 'points_per_game': points/len(games), 'form': points/(len(games)*3), 'avg_corners': 5.0}

leagues = sorted(df['League'].unique().tolist())
league = st.selectbox("Choose League", leagues)
teams_in_league = sorted(pd.concat([df[df['League']==league]['HomeTeam'], df[df['League']==league]['AwayTeam']]).unique().tolist())

col1, col2 = st.columns(2)
with col1:
    home_team = st.selectbox("Home Team", teams_in_league)
with col2:
    away_options = [t for t in teams_in_league if t != home_team]
    away_team = st.selectbox("Away Team", away_options)

if st.button("Predict Match", type="primary"):
    home = get_team_stats(home_team, league)
    away = get_team_stats(away_team, league)
    features = {}
    features['home_avg_goals_scored'] = home['avg_goals_scored']
    features['home_avg_goals_conceded'] = home['avg_goals_conceded']
    features['home_win_rate'] = home['win_rate']
    features['home_points_per_game'] = home['points_per_game']
    features['home_form'] = home['form']
    features['home_avg_corners'] = home['avg_corners']
    features['away_avg_corners'] = away['avg_corners']
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
    features['corners_diff'] = home['avg_corners'] - away['avg_corners']
    features['total_avg_corners'] = home['avg_corners'] + away['avg_corners']
    row = []
    for col in feature_columns:
        row.append(features.get(col, 0))
    X = pd.DataFrame([row], columns=feature_columns)
    prediction = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    classes = list(model.classes_)
    label_map = {'H': f'{home_team} Win', 'D': 'Draw', 'A': f'{away_team} Win'}
    st.success(f"### Prediction: {label_map.get(prediction, prediction)}")
    st.write("**Match Result Probabilities:**")
    for i, cls in enumerate(classes):
        name = label_map.get(cls, cls)
        st.write(f"{name}: {proba[i]*100:.1f}%")
        st.progress(float(proba[i]))
    c1, c2, c3 = st.columns(3)
    c1.metric("Home Form", f"{home['form']:.2f}")
    c2.metric("Away Form", f"{away['form']:.2f}")
    c3.metric("Home Goals / Game", f"{home['avg_goals_scored']:.2f} vs {away['avg_goals_scored']:.2f}")
    st.write("---")
    st.write("### Goals Over / Under 2.5")
    try:
        ou_model = joblib.load('models/over_under_model.pkl')
        ou_proba = ou_model.predict_proba(X)[0]
        over_prob = ou_proba[1] if len(ou_proba) > 1 else 0
        st.write(f"Over 2.5 Goals: {over_prob*100:.1f}%")
        st.progress(float(over_prob))
        st.write(f"Under 2.5 Goals: {(1-over_prob)*100:.1f}%")
        st.progress(float(1-over_prob))
        if over_prob > 0.55:
            st.info("Tip: Over 2.5 Goals looks likely")
        elif over_prob < 0.45:
            st.info("Tip: Under 2.5 Goals looks likely")
    except Exception as e:
        st.write("Train Over/Under model first - run train.py")
    st.write("### Corners Over / Under 9.5")
    if league in ['UCL', 'UEL']:
        st.write("Corners not available for this league")
    else:
        try:
            c_model = joblib.load('models/corners_model.pkl')
            c_proba = c_model.predict_proba(X)[0]
            c_over = c_proba[1] if len(c_proba) > 1 else 0
            st.write(f"Over 9.5 Corners: {c_over*100:.1f}%")
            st.progress(float(c_over))
            st.write(f"Under 9.5 Corners: {(1-c_over)*100:.1f}%")
        except:
            st.warning("No corners model yet")