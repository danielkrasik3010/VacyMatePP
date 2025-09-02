
import os
import json
import datetime
from typing import Optional
from urllib.parse import urlparse
from serpapi import GoogleSearch
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
        query = f"Events in {location}"
        if event_type:
            query += f" {event_type}"

        params = {
            "engine": "google_events",
            "q": query,
            "htichips": f"date:{start_date}_{end_date}",
            "api_key": SERPAPI_API_KEY
        }
        results = GoogleSearch(params).get_dict().get("events_results", [])[:20]
        simplified = [
            {
                "title": r.get("title"),
                "date": r.get("date"),
                "venue": r.get("venue_name"),
                "link": r.get("link")
            } for r in results
        ]
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

