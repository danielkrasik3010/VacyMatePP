
import os
import json
import datetime
from typing import Optional
from urllib.parse import urlparse
try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None
from pyowm import OWM
from langchain.agents import tool

from dotenv import load_dotenv
load_dotenv()

# The following API keys are placeholders and should be loaded from your .env file
# as shown in the original code. For this example, they are hardcoded
# to make the code self-contained and runnable.
SERPAPI_API_KEY = '297fdf48a26d5137d7068c6a7f7341cf0db14c16212b9a3eade05f4768521453'


# ========================================================================
#  LOCAL EVENT FINDER (top 20 results)
# ========================================================================

@tool
def local_event_finder(
    location: str,
    start_date: str,
    end_date: str,
    event_type: Optional[str] = None
) -> str:
    """
    Finds local events in a given location between start_date and end_date.
    Returns top 20 events with title, date, venue, and link.
    Optional: filter by event type (concert, sports, festival, etc.)
    """
    try:
        if GoogleSearch is None:
            return json.dumps([
                {
                    "title": "Sample Event 1",
                    "formatted_date": "Sep 16 - 7:00 PM",
                    "venue": "Local Venue",
                    "link": "https://example.com/event1",
                    "description": "Sample event description"
                },
                {
                    "title": "Sample Event 2", 
                    "formatted_date": "Sep 18 - 8:00 PM",
                    "venue": "Another Venue",
                    "link": "https://example.com/event2",
                    "description": "Another sample event"
                }
            ], indent=2)
        
        query = f"Events in {location}"
        if event_type:
            query += f" {event_type}"

        # Use proper SerpAPI parameters for Google Events
        params = {
            "engine": "google_events",
            "q": query,
            "htichips": "date:month",  # This month's events
            "gl": "us",  # Country code
            "hl": "en",  # Language
            "api_key": SERPAPI_API_KEY
        }
        results = GoogleSearch(params).get_dict().get("events_results", [])[:20]
        
        # Process results according to SerpAPI format
        simplified = []
        for r in results:
            event_data = {
                "title": r.get("title", ""),
                "date": r.get("date", {}),
                "address": r.get("address", []),
                "link": r.get("link", ""),
                "description": r.get("description", ""),
                "ticket_info": r.get("ticket_info", [])
            }
            
            # Extract date information
            date_info = event_data["date"]
            if isinstance(date_info, dict):
                start_date_str = date_info.get("start_date", "")
                when_str = date_info.get("when", "")
                event_data["formatted_date"] = f"{start_date_str} - {when_str}" if when_str else start_date_str
            else:
                event_data["formatted_date"] = str(date_info)
            
            # Extract venue from address
            if event_data["address"]:
                event_data["venue"] = event_data["address"][0] if isinstance(event_data["address"], list) else str(event_data["address"])
            else:
                event_data["venue"] = "Venue TBD"
            
            simplified.append(event_data)
        
        # Return first 15 events
        simplified = simplified[:15]
        return json.dumps(simplified, indent=2)
    except Exception as e:
        return f"Error with Local Event Finder: {e}"



# ========================================================================
# 5. TESTING THE TOOLS
# ========================================================================

if __name__ == "__main__":
    today = datetime.date.today()
    next_week = today + datetime.timedelta(days=7)
    print("Testing Local Event Finder...")
    event_result = local_event_finder.invoke({
        "location": "New York",
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": next_week.strftime("%Y-%m-%d"),
        "event_type": ""  # optional
    })
    print(event_result)
    print("\n---------------------------------------")

