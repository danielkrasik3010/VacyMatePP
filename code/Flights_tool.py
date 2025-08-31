from langchain.agents import tool
import requests

# Step 1: Function to simplify the raw API response
def minutes_to_hm(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

def simplify_itineraries(raw_response):
    simplified = {"itineraries": []}

    for itin in raw_response.get("itineraries", []):
        simplified_itin = {
            "id": itin.get("id"),
            "priceUSD": float(itin.get("price", {}).get("amount", 0)),
            "priceEUR": float(itin.get("priceEur", {}).get("amount", 0)),
            "durationOutbound": itin.get("outbound", {}).get("duration"),
            "durationInbound": itin.get("inbound", {}).get("duration"),
            "lastAvailableSeats": itin.get("lastAvailable", {}).get("seatsLeft"),
            "outbound": {},
            "inbound": {},
            "bookingUrl": None
        }

        # Outbound flight details
        outbound = itin.get("outbound", {}).get("sectorSegments", [])
        if outbound:
            seg = outbound[0].get("segment", {})
            simplified_itin["outbound"] = {
                "source": seg.get("source", {}).get("station", {}).get("name"),
                "sourceCode": seg.get("source", {}).get("station", {}).get("code"),
                "destination": seg.get("destination", {}).get("station", {}).get("name"),
                "destinationCode": seg.get("destination", {}).get("station", {}).get("code"),
                "departureLocalTime": seg.get("source", {}).get("localTime"),
                "arrivalLocalTime": seg.get("destination", {}).get("localTime"),
                "carrier": seg.get("carrier", {}).get("name"),
                "carrierCode": seg.get("carrier", {}).get("code"),
                "cabinClass": seg.get("cabinClass")
            }

        # Inbound flight details
        inbound = itin.get("inbound", {}).get("sectorSegments", [])
        if inbound:
            seg = inbound[0].get("segment", {})
            simplified_itin["inbound"] = {
                "source": seg.get("source", {}).get("station", {}).get("name"),
                "sourceCode": seg.get("source", {}).get("station", {}).get("code"),
                "destination": seg.get("destination", {}).get("station", {}).get("name"),
                "destinationCode": seg.get("destination", {}).get("station", {}).get("code"),
                "departureLocalTime": seg.get("source", {}).get("localTime"),
                "arrivalLocalTime": seg.get("destination", {}).get("localTime"),
                "carrier": seg.get("carrier", {}).get("name"),
                "carrierCode": seg.get("carrier", {}).get("code"),
                "cabinClass": seg.get("cabinClass")
            }

        # Booking URL
        booking_edges = itin.get("bookingOptions", {}).get("edges", [])
        if booking_edges:
            simplified_itin["bookingUrl"] = booking_edges[0].get("node", {}).get("bookingUrl")

        simplified["itineraries"].append(simplified_itin)

    return simplified

# Step 2: Create the LangChain tool
@tool
def get_flight_prices(source: str, destination: str, adults: int = 1, currency: str = "USD") -> dict:
    """
    Get flight prices from Kiwi.com API via RapidAPI and return a simplified JSON.
    """
    url = "https://kiwi-com-cheap-flights.p.rapidapi.com/round-trip"

    querystring = {
        "source": source,
        "destination": destination,
        "currency": currency.lower(),
        "locale": "en",
        "adults": str(adults),
        "children": "0",
        "infants": "0",
        "handbags": "1",
        "holdbags": "0",
        "cabinClass": "ECONOMY",
        "sortBy": "QUALITY",
        "sortOrder": "ASCENDING",
        "applyMixedClasses": "true",
        "allowReturnFromDifferentCity": "true",
        "allowChangeInboundDestination": "true",
        "allowChangeInboundSource": "true",
        "allowDifferentStationConnection": "true",
        "enableSelfTransfer": "true",
        "allowOvernightStopover": "true",
        "enableTrueHiddenCity": "true",
        "enableThrowAwayTicketing": "true",
        "outbound": "SUNDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY,MONDAY,TUESDAY",
        "transportTypes": "FLIGHT",
        "contentProviders": "FLIXBUS_DIRECTS,FRESH,KAYAK,KIWI",
        "limit": "1"
    }

    headers = {
        "x-rapidapi-key": "accc99e318msh4c97e17ee7eaf7ep1b9127jsn901e342a67df",
        "x-rapidapi-host": "kiwi-com-cheap-flights.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    try:
        raw_json = response.json()
        return simplify_itineraries(raw_json)
    except Exception as e:
        return {"error": str(e)}

# Step 3: Test the tool
if __name__ == "__main__":
    params = {
        "source": "Country:GB",
        "destination": "City:dubrovnik_hr",
        "adults": 1,
        "currency": "USD"
    }

    # Call the tool using .invoke()
    result = get_flight_prices.invoke(params)
    import json
    print(json.dumps(result, indent=2))