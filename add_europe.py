import requests
import pandas as pd
from datetime import date, timedelta

leagues = {
    'UCL': 'uefa.champions',
    'UEL': 'uefa.europa',
    'UECL': 'uefa.europa.conf',
}

all_rows = []
start = date(2025, 9, 1)
end = date(2025, 11, 24)

for league_name, slug in leagues.items():
    print(f"Fetching {league_name}...")
    seen = set()
    d = start
    total = 0
    while d <= end:
        datestr = d.strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={datestr}"
        try:
            r = requests.get(url, timeout=15)
            data = r.json()
            for ev in data.get('events', []):
                eid = ev.get('id')
                if eid in seen:
                    continue
                seen.add(eid)
                try:
                    comp = ev['competitions'][0]
                    if comp['status']['type']['completed'] != True:
                        continue
                    home = comp['competitors'][0]
                    away = comp['competitors'][1]
                    # ESPN sometimes swaps home/away, fix by homeAway
                    if home.get('homeAway') != 'home':
                        home, away = away, home
                    hs = int(home['score'])
                    aws = int(away['score'])
                    all_rows.append({
                        'Date': ev['date'][:10],
                        'League': league_name,
                        'HomeTeam': home['team']['displayName'],
                        'AwayTeam': away['team']['displayName'],
                        'FTHG': hs,
                        'FTAG': aws,
                        'FTR': 'H' if hs > aws else 'A' if aws > hs else 'D',
                        'Season': '2025-26',
                        'HC': None,
                        'AC': None,
                    })
                    total += 1
                except:
                    continue
        except Exception as e:
            pass
        d += timedelta(days=1)
    print(f"{league_name}: added {total} games")

if all_rows:
    europe_df = pd.DataFrame(all_rows)
    old_df = pd.read_csv('data/raw/all_leagues.csv')
    combined = pd.concat([old_df, europe_df], ignore_index=True)
    combined.to_csv('data/raw/all_leagues.csv', index=False)
    print("SAVED!")
    print(combined['League'].value_counts())
else:
    print("No Europe data found")
