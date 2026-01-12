import asyncio

import aiohttp
import requests

# 1. Get the Token (Synchronous part is fine for now)
AUTH_ENDPOINT = "https://test.api.amadeus.com/v1/security/oauth2/token"
headers_auth = {"Content-Type": "application/x-www-form-urlencoded"}
data_auth = {
    "grant_type": "client_credentials",
    "client_id": "ytzL0WxJ22AdQAxgQW6q7jrndGvDqpIP",  # Replace with your actual ID
    "client_secret": "xLKAu72gg6FDa6gZ",  # Replace with your actual Secret
}


response = requests.post(AUTH_ENDPOINT, headers=headers_auth, data=data_auth)

# Check if auth worked before proceeding
if response.status_code != 200:
    print(f"Auth failed: {response.text}")
    exit()

access_token = response.json()["access_token"]


async def main():
    # 2. Set up headers for the search
    # Content-Type is usually added automatically by aiohttp when using json=,
    # but adding it explicitly is good practice.
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json",
    }

    flight_search_endpoint = "https://test.api.amadeus.com/v2/shopping/flight-offers"

    # 3. FIX: This is now a Python Dictionary, NOT a string (removed """)
    parameters = {
        "currencyCode": "USD",  # Added currency just in case
        "originDestinations": [
            {
                "id": "1",
                "originLocationCode": "JFK",
                "destinationLocationCode": "COK",
                "departureDateTimeRange": {"date": "2026-02-03"},
            }
        ],
        "travelers": [
            {"id": "1", "travelerType": "ADULT", "fareOptions": ["STANDARD"]}
        ],
        "sources": ["GDS"],
        "searchCriteria": {"maxFlightOffers": 1},
    }

    async with aiohttp.ClientSession() as session:
        # 4. FIX: Changed session.get -> session.post
        # We pass the dictionary 'parameters' to the 'json' argument.
        async with session.post(
            flight_search_endpoint, json=parameters, headers=headers
        ) as resp:
            # 5. Read the response
            flights = await resp.json()

            # Pretty print for easier debugging
            import json

            print(json.dumps(flights, indent=2))


asyncio.run(main())
