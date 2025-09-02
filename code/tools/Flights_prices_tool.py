from langchain.agents import tool
import requests
import os
from dotenv import load_dotenv
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
) -> dict:
    """
    Fetches round-trip flight itineraries from the Kiwi API based on provided source, destination,
    number of adults, currency, and required outbound/inbound departure date ranges.
    Returns a simplified JSON with itinerary details including prices, flight durations,
    seat availability, outbound/inbound flight details, and a human-readable summary.
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
        "limit": "1",
        "outboundDepartureDateStart": outboundDepartureDateStart,
        "outboundDepartureDateEnd": outboundDepartureDateEnd,
        "inboundDepartureDateStart": inboundDepartureDateStart,
        "inboundDepartureDateEnd": inboundDepartureDateEnd
    }

    headers = {
        "x-rapidapi-key": os.getenv("FLIGHTS_RAPID_API_KEY"),
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
