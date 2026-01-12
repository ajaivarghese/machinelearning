import asyncio
import json

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
    # 2. Set up headers (Shared for both Search and Pricing)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Define Endpoints
    search_endpoint = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    pricing_endpoint = "https://test.api.amadeus.com/v1/shopping/flight-offers/pricing"

    # --- STEP 1: SEARCH FOR FLIGHTS ---
    search_params = {
        "currencyCode": "USD",
        "originDestinations": [
            {
                "id": "1",
                "originLocationCode": "JFK",
                "destinationLocationCode": "COK",  # Changed to LHR for better test data availability
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
        print("Searching for flights...")
        async with session.post(
            search_endpoint, json=search_params, headers=headers
        ) as resp:
            search_data = await resp.json()

            # Check if we got any offers
            if "data" not in search_data or not search_data["data"]:
                print("No flight offers found.")
                print(json.dumps(search_data, indent=2))
                return

            # Select the first offer to price
            selected_offer = search_data["data"][0]
            print(
                f"Found offer ID: {selected_offer['id']} - Price: {selected_offer['price']['total']}"
            )

        # --- STEP 2: PRICE THE SELECTED OFFER ---
        # The Pricing API requires the offer to be wrapped in a specific JSON structure
        pricing_payload = {
            "data": {"type": "flight-offers-pricing", "flightOffers": [selected_offer]}
        }

        print("\nConfirming price (Pricing API)...")
        async with session.post(
            pricing_endpoint, json=pricing_payload, headers=headers
        ) as resp:
            pricing_data = await resp.json()

            # Pretty print the final priced offer
            print(json.dumps(pricing_data, indent=2))


asyncio.run(main())
