import os
import json
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from serpapi import GoogleSearch
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
load_dotenv()
# --- API Key setup ---

if not os.getenv("SERPAPI_API_KEY"):
    raise ValueError("SERPAPI_API_KEY environment variable not set.")

# --- Define the tool's input schema ---
class HotelSearchInput(BaseModel):
    query: str = Field(..., description="The city, region, or specific hotel to search for.")
    check_in_date: date = Field(..., description="The check-in date for the hotel stay. Format: YYYY-MM-DD.")
    check_out_date: date = Field(..., description="The check-out date for the hotel stay. Format: YYYY-MM-DD.")
    adults: Optional[int] = Field(2, description="The number of adults. Defaults to 2.")
    children: Optional[int] = Field(0, description="The number of children. Defaults to 0.")

def simplify_hotels(hotels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extracts valuable fields, parses numeric prices, formats addresses, and generates human-readable summaries."""
    simplified = []

    for h in hotels:
        # Helper to parse numeric price
        def parse_price(price_str):
            if price_str:
                return float(price_str.replace('$','').replace(',',''))
            return None

        price_per_night = h.get("rate_per_night", {}).get("lowest")
        total_price = h.get("total_rate", {}).get("lowest")

        price_per_night_val = parse_price(price_per_night)
        total_price_val = parse_price(total_price)

        # Address formatting
        gps = h.get("gps_coordinates", {})
        lat = gps.get("latitude")
        lon = gps.get("longitude")
        formatted_address = f"{lat}, {lon}" if lat and lon else "N/A"

        rating = h.get("overall_rating")
        hotel_class = h.get("hotel_class")

        # Build simplified hotel dict
        hotel = {
            "name": h.get("name"),
            "description": h.get("description"),
            "rating": round(rating, 1) if rating else None,
            "hotel_class": hotel_class,
            "price": {
                "per_night": price_per_night,
                "per_night_value": price_per_night_val,
                "total": total_price,
                "total_value": total_price_val
            },
            "address": {
                "latitude": lat,
                "longitude": lon,
                "formatted": formatted_address
            },
            "check_in": h.get("check_in_time"),
            "check_out": h.get("check_out_time"),
        }

        # Human-readable summary
        summary_parts = [
            hotel["name"],
            f"({hotel_class})" if hotel_class else "",
            f"{hotel['rating']}★" if hotel["rating"] else "",
            f"From ${price_per_night_val}/night" if price_per_night_val else "",
            f"(total ${total_price_val})" if total_price_val else "",
            f"Near {formatted_address}"
        ]
        hotel["summary"] = " ".join([p for p in summary_parts if p])

        simplified.append(hotel)

    return simplified


# --- LangChain Tool ---
@tool(args_schema=HotelSearchInput)
def hotel_search(query: str, check_in_date: date, check_out_date: date, adults: int = 2, children: int = 0, sort_by: Optional[str] = None) -> dict:
    """
    Searches for hotels using Google Hotels (via SerpApi).
    Returns simplified JSON with key details + human-readable summaries.
    """
    params = {
        "engine": "google_hotels",
        "q": query,
        "check_in_date": check_in_date.strftime('%Y-%m-%d'),
        "check_out_date": check_out_date.strftime('%Y-%m-%d'),
        "adults": str(adults),
        "children": str(children),
        "currency": "USD",
        "gl": "us",
        "hl": "en",
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            return {"error": results["error"]}

        # Collect hotels from all possible keys
        raw_hotels = results.get("properties", []) + results.get("featured_hotels", []) + results.get("other_hotels", [])

        simplified_hotels = simplify_hotels(raw_hotels)

        return {
            "query": query,
            "check_in": check_in_date.isoformat(),
            "check_out": check_out_date.isoformat(),
            "total_found": len(raw_hotels),
            "hotels": simplified_hotels,
        }

    except Exception as e:
        return {"error": f"Failed to perform hotel search: {str(e)}"}


# --- Test the tool ---
if __name__ == "__main__":
    test_params = {
        "query": "Paris",
        "gl": "us",
        "hl": "en",
        'currency': "USD",
        "check_in_date": date(2025, 9, 20),
        "check_out_date": date(2025, 9, 25),
        "adults": 2,
        "children": 0,
    }

    result = hotel_search.invoke(test_params)
    print(json.dumps(result, indent=2))
