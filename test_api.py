
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

if not API_KEY:
    print("ERROR: API key not found in .env")
    raise SystemExit

url = "https://v3.football.api-sports.io/status"

headers = {
    "x-apisports-key": API_KEY
}

try:
    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    print("HTTP STATUS:", response.status_code)

    try:
        data = response.json()

        if response.status_code == 200:
            print("\nAPI RESPONSE:")
            print(data)
        else:
            # Do not print your API key.
            print("\nAPI ERROR:")
            print(data.get("errors", data))

    except ValueError:
        print("Response was not JSON.")
        print(response.text[:500])

except requests.RequestException as error:
    print("Connection error:", error)
