import asyncio
import json

import aiohttp
import requests

# --- CONFIGURATION ---
CLIENT_ID = "ytzL0WxJ22AdQAxgQW6q7jrndGvDqpIP"  # Replace with your API Key
CLIENT_SECRET = "xLKAu72gg6FDa6gZ"  # Replace with your API Secret
BASE_URL = "https://test.api.amadeus.com"


# 1. AUTHENTICATION (Synchronous for simplicity)
def get_access_token():
    url = f"{BASE_URL}/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Auth failed: {response.text}")


async def book_flight():
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        # --- STEP 1: SEARCH ---
        print("\n1. Searching for flights (JFK -> LHR)...")
        search_url = f"{BASE_URL}/v2/shopping/flight-offers"
        search_body = {
            "currencyCode": "USD",
            "originDestinations": [
                {
                    "id": "1",
                    "originLocationCode": "JFK",
                    "destinationLocationCode": "LHR",
                    "departureDateTimeRange": {"date": "2026-03-10"},
                }
            ],
            "travelers": [{"id": "1", "travelerType": "ADULT"}],
            "sources": ["GDS"],
            "searchCriteria": {"maxFlightOffers": 1},
        }

        async with session.post(search_url, json=search_body, headers=headers) as resp:
            search_data = await resp.json()
            if not search_data.get("data"):
                print("No flights found.")
                return
            initial_offer = search_data["data"][0]
            print(
                f"   Found flight: {initial_offer['itineraries'][0]['segments'][0]['carrierCode']} - ${initial_offer['price']['total']}"
            )

        # --- STEP 2: PRICING (Validation) ---
        print("\n2. Confirming Price & Availability...")
        pricing_url = f"{BASE_URL}/v1/shopping/flight-offers/pricing"
        pricing_body = {
            "data": {"type": "flight-offers-pricing", "flightOffers": [initial_offer]}
        }

        async with session.post(
            pricing_url, json=pricing_body, headers=headers
        ) as resp:
            price_data = await resp.json()
            if "data" not in price_data:
                print(f"Pricing failed: {price_data}")
                return

            # CRITICAL: We must use the offer returned by PRICING, not search
            final_offer = price_data["data"]["flightOffers"][0]
            print("   Price confirmed.")

        # --- STEP 3: CREATE ORDER (Booking) ---
        print("\n3. Creating Flight Order (Booking)...")
        order_url = f"{BASE_URL}/v1/booking/flight-orders"

        # We need to construct a "traveler" object matching the ID in the offer
        order_body = {
            "data": {
                "type": "flight-order",
                "flightOffers": [final_offer],
                "travelers": [
                    {
                        "id": "1",
                        "dateOfBirth": "1990-01-01",
                        "name": {"firstName": "JANE", "lastName": "DOE"},
                        "gender": "FEMALE",
                        "contact": {
                            "emailAddress": "jane.doe@example.com",
                            "phones": [
                                {
                                    "deviceType": "MOBILE",
                                    "countryCallingCode": "1",
                                    "number": "5555555555",
                                }
                            ],
                        },
                    }
                ],
            }
        }

        async with session.post(order_url, json=order_body, headers=headers) as resp:
            order_data = await resp.json()

            if resp.status == 201:
                print("\nSUCCESS! Flight Booked.")
                print(f"Booking ID: {order_data['data']['id']}")
                print(
                    f"PNR (Reference): {order_data['data']['associatedRecords'][0]['reference']}"
                )
            else:
                print("\nBooking Failed.")
                print(json.dumps(order_data, indent=2))


# Run the async loop
asyncio.run(book_flight())
