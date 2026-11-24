import requests
import pandas as pd

API_KEY = "PASTE_YOUR_API_KEY_HERE"  # <-- put your key here
headers = {"x-apisports-key": API_KEY}

# API-Football IDs: 2=UCL, 3=UEL, 848=UECL (Conference League)
leagues = {
    'UCL': (2, 2025),
    'UEL': (3, 2025),
    'UECL': (848, 2025),
}

all_rows = []
for league_name, (league_id, season) in leagues.items():
    url = "https://v3.football.api-sports.io/fixtures"
    params = {"league": league_id, "season": season}
    r = requests.get(url, headers=headers, params=params)
    data = r.json().get('response', [])
    print(f"{league_name}: {len(data)} games from API")
    for m in data:
        if m['fixture']['status']['short'] != 'FT':
            continue
        all_rows.append({
            'Date': m['fixture']['date'][:10],
            'League': league_name,
            'HomeTeam': m['teams']['home']['name'],
            'AwayTeam': m['teams']['away']['name'],
            'FTHG': m['goals']['home'],
            'FTAG': m['goals']['away'],
            'FTR': 'H' if m['goals']['home'] > m['goals']['away'] else 'A' if m['goals']['away'] > m['goals']['home'] else 'D',
            'Season': '2025-26',
            'HC': None,  # No corners for Europe
            'AC': None,
        })

if all_rows:
    europe_df = pd.DataFrame(all_rows)
    old_df = pd.read_csv('data/raw/all_leagues.csv')
    combined = pd.concat([old_df, europe_df], ignore_index=True)
    combined.to_csv('data/raw/all_leagues.csv', index=False)
    print(f"SAVED! Total now: {len(combined)} games")
    print(combined['League'].value_counts())