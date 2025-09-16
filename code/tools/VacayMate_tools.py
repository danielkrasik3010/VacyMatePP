# VacayMate_tools.py (inside code/tools/)
import sys
import os
from typing import Any, List, Dict

# Ensure project root is discoverable when importing this module directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_tools() -> List[Dict[str, Any]]:
    """
    Initializes and returns a list of all available tools for the VacayMate system.
    We import tool modules here (deferred) to avoid circular imports during module import time.
    """
    # Deferred imports to avoid circular import issues
    from code.tools import (
        destination_info_tool,
        Event_finder_tool,
        Flights_prices_tool,
        Hotels_prices_tool,
        Make_quotation_tool,
        Weather_Forecast_tool,
        city_mapping,
    )

    return [
        {
            "name": "get_destination_info",
            "func": destination_info_tool.get_destination_info,
            "description": "Get information about a destination including attractions and activities"
        },
        {
            "name": "search_events",
            "func": Event_finder_tool.search_events,
            "description": "Search for events and activities in a specific location and date range"
        },
        {
            "name": "get_weather_forecast",
            "func": Weather_Forecast_tool.get_weather_forecast,
            "description": "Get weather forecast for a specific location and date range"
        },
        {
            "name": "search_flights",
            "func": Flights_prices_tool.get_flight_prices,
            "description": "Search for flights between two locations and date ranges"
        },
        {
            "name": "hotel_search",
            "func": Hotels_prices_tool.hotel_search,
            "description": "Search for hotels in a specific location"
        },
        {
            "name": "make_quotation",
            "func": Make_quotation_tool.make_quotation,
            "description": "Generate a quotation for the vacation including flights, hotels, and activities"
        }
    ]


if __name__ == "__main__":
    # Example usage for testing purposes
    print("Available tools:")
    for tool in get_tools():
        print(f"- {tool['name']}: {tool['description']}")
