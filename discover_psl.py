
import os
import requests
from dotenv import load_dotenv

load_dotenv()

headers = {
    "x-apisports-key": os.getenv("API_FOOTBALL_KEY")
}

url = "https://v3.football.api-sports.io/leagues"

searches = [
    "South Africa",
    "PSL",
    "Betway Premiership"
]

for name in searches:

    print("\nSearching:", name)

    response = requests.get(
        url,
        headers=headers,
        params={"search": name},
        timeout=30
    )

    data = response.json()

    print("HTTP:", response.status_code)

    if response.status_code != 200:
        print(data.get("errors"))
        continue

    for item in data.get("response", []):

        league = item["league"]
        country = item["country"]

        print(
            "ID:", league["id"],
            "| Name:", league["name"],
            "| Country:", country["name"]
        )
