
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

if not API_KEY or API_KEY == "PASTE_YOUR_API_KEY_HERE":
    raise RuntimeError("Add your API key to the .env file.")

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Competition names and countries used for API lookup.
COMPETITIONS = [
    ("PSL", "Premier Soccer League", "South Africa"),
    ("EPL", "Premier League", "England"),
    ("LEAGUE_ONE", "League One", "England"),
    ("UCL", "UEFA Champions League", None),
    ("UEL", "UEFA Europa League", None),
("UECL": { "name": "UEFA Conference League","country": None ,"id": 848}),

]

SEASONS = range(2022, 2025)

session = requests.Session()
session.headers.update(HEADERS)



def api_get(endpoint, params):

    for attempt in range(3):

        response = session.get(
            BASE_URL + endpoint,
            params=params,
            timeout=45
        )

        if response.status_code == 429:

            wait = int(
                response.headers.get("Retry-After", "60")
            )

            if attempt == 2:
                raise RuntimeError(
                    "API rate limit reached. "
                    "Wait before downloading again."
                )

            print(f"Rate limited. Waiting {wait} seconds...")
            time.sleep(max(wait, 60))
            continue

        response.raise_for_status()

        result = response.json()

        if result.get("errors"):
            raise RuntimeError(str(result["errors"]))

        time.sleep(6)

        return result.get("response", [])

    raise RuntimeError("API request failed.")




def find_competition(name, country):

    # API does not allow country + search together.
    results = api_get(
        "/leagues",
        {"search": name}
    )

    matches = [
        item for item in results
        if item["league"]["name"].lower() == name.lower()
    ]

    if country:
        matches = [
            item for item in matches
            if item["country"]["name"].lower() == country.lower()
        ]

    if not matches:
        raise RuntimeError(
            f"Competition not found: {name} ({country})"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple competitions found: {name}. "
            "Configure the correct league ID."
        )

    return matches[0]


    results = api_get("/leagues", params)

    matches = [
        item for item in results
        if item["league"]["name"].lower() == name.lower()
    ]

    if country:
        matches = [
            item for item in matches
            if item["country"]["name"].lower() == country.lower()
        ]

    if not matches:
        raise RuntimeError(
            f"Competition not found: {name} ({country})"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Ambiguous competition: {name}. "
            "Check API league IDs and configure explicitly."
        )

    return matches[0]


def download_fixtures(code, name, country):

    print(f"\nSearching for {name}...")

    competition = find_competition(name, country)
   
    league_id = competition["league"]["id"]

    available_seasons = {
        item["year"]
        for item in competition.get("seasons", [])
    }

    records = []

    for season in SEASONS:

        if season not in available_seasons:
            print(f"Season {season}: not listed by API")
            continue

        print(f"Downloading {name} {season}...")

        try:
            fixtures = api_get(
                "/fixtures",
                {
                    "league": league_id,
                    "season": season,
                    "status": "FT"
                }
            )

            count = 0

            for item in fixtures:

                fixture = item["fixture"]
                teams = item["teams"]
                goals = item["goals"]

                home_goals = goals["home"]
                away_goals = goals["away"]

                if home_goals is None or away_goals is None:
                    continue

                if home_goals > away_goals:
                    result = "H"
                elif home_goals < away_goals:
                    result = "A"
                else:
                    result = "D"

                records.append({
                    "Date": fixture["date"],
                    "League": code,
                    "HomeTeam": teams["home"]["name"],
                    "AwayTeam": teams["away"]["name"],
                    "FTHG": home_goals,
                    "FTAG": away_goals,
                    "FTR": result,
                    "Season": season
                })

                count += 1

            print(f"Downloaded {count} completed matches.")

        except Exception as error:
            print(f"Season download failed: {error}")

        time.sleep(1)

    return records


def main():

    all_records = []

    for code, name, country in COMPETITIONS:

        try:
            records = download_fixtures(
                code, name, country
            )

            all_records.extend(records)

        except Exception as error:
            print(f"\n{code} failed: {error}")

    if not all_records:
        raise RuntimeError(
            "No fixtures downloaded. Check API key, "
            "subscription and competition coverage."
        )

    df = pd.DataFrame(all_records)

    df["Date"] = pd.to_datetime(
        df["Date"], utc=True
    )

    df = df.drop_duplicates(
        subset=["League", "Date", "HomeTeam", "AwayTeam"]
    )

    df = df.sort_values("Date")

    output = DATA_DIR / "all_leagues.csv"

    df.to_csv(output, index=False)

    print("\n================================")
    print("MULTI-LEAGUE DOWNLOAD COMPLETE")
    print("================================")
    print("Total matches:", len(df))
    print("\nMatches by competition:")
    print(df.groupby("League").size())
    print("\nSaved to:", output)


if __name__ == "__main__":
    main()
