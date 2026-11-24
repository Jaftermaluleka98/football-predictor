import pandas as pd

urls = {
    'EPL': 'https://www.football-data.co.uk/mmz4281/2526/E0.csv',
    'LEAGUE_ONE': 'https://www.football-data.co.uk/mmz4281/2526/E2.csv',
}

all_dfs = []
for league_name, url in urls.items():
    try:
        df = pd.read_csv(url)
        print(f"{league_name}: {len(df)} games")
        df = df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HC', 'AC']]
        df['League'] = league_name
        df['Season'] = '2025-26'
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        all_dfs.append(df)
    except Exception as e:
        print(f"Failed {league_name}: {e}")

if all_dfs:
    final = pd.concat(all_dfs, ignore_index=True)
    final = final.dropna(subset=['HC', 'AC'])
    final.to_csv('data/raw/all_leagues.csv', index=False)
    print(f"SAVED! Total games with corners: {len(final)}")