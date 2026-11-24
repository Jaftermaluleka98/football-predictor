
import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("API_FOOTBALL_KEY")

headers = {
    "x-apisports-key": key
}

url = "https://v3.football.api-sports.io/leagues"

for search in ["Premier", "Conference"]:

    print("\nSearching:", search)

    response = requests.get(
        url,
        headers=headers,
        params={"search": search},
        timeout=30
    )

    print("HTTP:", response.status_code)

    if response.status_code != 200:
        print(response.text[:500])
        continue

    data = response.json()

    for item in data.get("response", []):

        league = item["league"]
        country = item["country"]

        if (
            country["name"] == "South Africa"
            or "Conference" in league["name"]
        ):
            print(
                "ID:", league["id"],
                "| Name:", league["name"],
                "| Country:", country["name"]
            )
