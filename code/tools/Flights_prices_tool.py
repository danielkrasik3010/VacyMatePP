from langchain.agents import tool
import requests
import os
from dotenv import load_dotenv
from .city_mapping import CITY_CODES

load_dotenv()

def minutes_to_hm(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

def simplify_itineraries(raw_response):
    simplified = {"itineraries": []}
    for itin in raw_response.get("itineraries", []):
        duration_outbound_minutes = itin.get("outbound", {}).get("duration", 0) // 60
        duration_inbound_minutes = itin.get("inbound", {}).get("duration", 0) // 60

        simplified_itin = {
            "id": itin.get("id"),
            "priceUSD": float(itin.get("price", {}).get("amount", 0)),
            "priceEUR": float(itin.get("priceEur", {}).get("amount", 0)),
            "durationOutbound": minutes_to_hm(duration_outbound_minutes),
            "durationInbound": minutes_to_hm(duration_inbound_minutes),
            "lastAvailableSeats": itin.get("lastAvailable", {}).get("seatsLeft"),
            "outbound": {},
            "inbound": {},
            "bookingUrl": None,
            "human_readable_summary": None
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
                "cabinClass": seg.get("cabinClass"),
                "summary": f"{seg.get('carrier', {}).get('name')} flight from "
                           f"{seg.get('source', {}).get('station', {}).get('name')} to "
                           f"{seg.get('destination', {}).get('station', {}).get('name')}, departing at "
                           f"{seg.get('source', {}).get('localTime')} and arriving at "
                           f"{seg.get('destination', {}).get('localTime')}"
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
                "cabinClass": seg.get("cabinClass"),
                "summary": f"{seg.get('carrier', {}).get('name')} flight from "
                           f"{seg.get('source', {}).get('station', {}).get('name')} to "
                           f"{seg.get('destination', {}).get('station', {}).get('name')}, departing at "
                           f"{seg.get('source', {}).get('localTime')} and arriving at "
                           f"{seg.get('destination', {}).get('localTime')}"
            }

        # Booking URL
        booking_edges = itin.get("bookingOptions", {}).get("edges", [])
        if booking_edges:
            simplified_itin["bookingUrl"] = booking_edges[0].get("node", {}).get("bookingUrl")

        # Human-readable summary
        outbound_summary = simplified_itin["outbound"].get("summary")
        inbound_summary = simplified_itin["inbound"].get("summary")
        price = simplified_itin["priceUSD"]
        seats = simplified_itin["lastAvailableSeats"]

        if outbound_summary and inbound_summary:
            simplified_itin["human_readable_summary"] = (
                f"The round-trip flight costs ${price:.2f}. "
                f"The outbound flight is: {outbound_summary}. "
                f"The inbound flight is: {inbound_summary}. "
                f"There are {seats} seats left."
            )
        elif outbound_summary:
            simplified_itin["human_readable_summary"] = (
                f"The one-way flight costs ${price:.2f}. "
                f"The flight is: {outbound_summary}. "
                f"There are {seats} seats left."
            )
        else:
            simplified_itin["human_readable_summary"] = f"A flight option costs ${price:.2f}, but detailed flight information is not available."

        simplified["itineraries"].append(simplified_itin)

    return simplified


# --- LangChain Tool with required dates ---
@tool
def get_flight_prices(
    source: str,
    destination: str,
    adults: int,
    currency: str,
    outboundDepartureDateStart: str,
    outboundDepartureDateEnd: str,
    inboundDepartureDateStart: str,
    inboundDepartureDateEnd: str
):
    """
    Fetches round-trip flight itineraries from the Kiwi API.
    
    Args:
        source: Source city (e.g., 'paris' or 'City:paris_fr')
        destination: Destination city (e.g., 'milan' or 'City:milan_it')
        adults: Number of adult passengers
        currency: Currency code (e.g., 'USD', 'EUR')
        outboundDepartureDateStart: Start date for outbound flight (YYYY-MM-DD)
        outboundDepartureDateEnd: End date for outbound flight (YYYY-MM-DD)
        inboundDepartureDateStart: Start date for return flight (YYYY-MM-DD)
        inboundDepartureDateEnd: End date for return flight (YYYY-MM-DD)
        
    Returns:
        dict: Flight information or error message
    """
    import re
    
    # Clean and format city codes
    def format_city_code(city_str):
        # If it's already in the correct format, return as is
        if isinstance(city_str, str) and city_str.startswith('City:'):
            return city_str
            
        # Clean the input string
        city_str = str(city_str).strip().lower()
        
        # Try to find matching city in our mapping
        for code in CITY_CODES:
            code_lower = code.lower()
            if city_str in code_lower:
                return code
                
        # If not found, try to construct a code
        parts = re.split(r'[,_-]', city_str)
        if len(parts) >= 2:
            return f'City:{parts[0]}_{parts[-1][:2]}'  # e.g., 'milan_it'
        
        # Last resort: return as is with a warning
        print(f"Warning: Could not find city code for: {city_str}")
        return f'City:{city_str}'
    
    # Format source and destination
    source = format_city_code(source)
    destination = format_city_code(destination)

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
        "limit": "10",
        "outboundDepartureDateStart": outboundDepartureDateStart,
        "outboundDepartureDateEnd": outboundDepartureDateEnd,
        "inboundDepartureDateStart": inboundDepartureDateStart,
        "inboundDepartureDateEnd": inboundDepartureDateEnd
    }

    headers = {
        "x-rapidapi-key": os.getenv("FLIGHTS_RAPID_API_KEY"),
        "x-rapidapi-host": "kiwi-com-cheap-flights.p.rapidapi.com"
    }

    # Log the actual request being made for debugging
    print(f"Searching flights from {source} to {destination}")
    print(f"Outbound: {outboundDepartureDateStart} to {outboundDepartureDateEnd}")
    print(f"Inbound: {inboundDepartureDateStart} to {inboundDepartureDateEnd}")

    response = requests.get(url, headers=headers, params=querystring)

    try:
        # Debug the API response
        print(f"DEBUG - API Response Status: {response.status_code}")
        print(f"DEBUG - API Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            return {"error": f"API returned status {response.status_code}: {response.text}"}
        
        raw_json = response.json()
        print(f"DEBUG - Raw API Response: {str(raw_json)[:500]}...")
        
        simplified = simplify_itineraries(raw_json)
        
        # Add debug info to see how many flights were returned
        total_flights = len(simplified.get("itineraries", []))
        simplified["debug_info"] = {
            "total_flights_found": total_flights,
            "api_limit_requested": 20,
            "source_formatted": source,
            "destination_formatted": destination,
            "api_status_code": response.status_code,
            "raw_response_keys": list(raw_json.keys()) if isinstance(raw_json, dict) else "not_dict"
        }
        
        return simplified
    except Exception as e:
        return {"error": f"Exception in flight search: {str(e)}", "response_text": response.text[:200] if response else "No response"}


# Step 3: Test the tool
if __name__ == "__main__":
    params = {
        "source": "City:warsaw_pl",
        "destination": "City:dubrovnik_hr",
        "adults": 1,
        "currency": "USD",
        "outboundDepartureDateStart": "2025-09-15T00:00:00",
        "outboundDepartureDateEnd": "2025-09-15T23:59:59",
        "inboundDepartureDateStart": "2025-09-20T00:00:00",
        "inboundDepartureDateEnd": "2025-09-20T23:59:59"
    }

    result = get_flight_prices.invoke(params)

    import json
    print(json.dumps(result, indent=2))
