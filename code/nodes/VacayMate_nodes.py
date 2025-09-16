import json
import datetime
import sys
import os
from typing import TypedDict, Optional, Any, Dict
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from typing_extensions import Annotated
import operator
from datetime import datetime
from langgraph.graph.message import AnyMessage, add_messages
import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# --- Setup logging to both console and file ---
log_dir = os.path.join(
    os.path.dirname(__file__), "..", "..", "outputs"
)
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(
    log_dir,
    f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)

class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    def flush(self, *args, **kwargs):
        self.terminal.flush()
        self.log.flush()

    def info(self, message):
        self.write(f"INFO:__main__:{message}\n")

    def error(self, message):
        self.write(f"ERROR:__main__:{message}\n")

sys.stdout = Logger(log_file)
# ------------------ End Logging Setup ------------------

# Import the actual tools to be used by the agents
from tools.Flights_prices_tool import get_flight_prices
from tools.Hotels_prices_tool import hotel_search
from tools.destination_info_tool import get_destination_info
from tools.Event_finder_tool import search_events
from tools.Make_quotation_tool import make_quotation
from tools.Weather_Forecast_tool import get_weather_forecast
from tools.city_mapping import get_city_code
from consts import (
    MANAGER,
    RESEARCHER,
    PLANNER,
    CALCULATOR,
    SUMMARIZER,
    MERGE_RESULTS,
)

# Helper function to format currency
def format_currency(value, currency, locale_name='en_US.UTF-8'):
    if not isinstance(value, (int, float)):
        return "N/A"
    return locale.currency(value, symbol=True, grouping=True)


def run_manager(state: Dict[str, Any]) -> Dict[str, Any]:
    print("🎬 Manager Agent: Starting...")
    user_request = state["user_request"]
    destination = state["destination"]
    
    manager_message = f"User request received: {user_request}. Planning trip to {destination}."
    print("   - Manager decided to start the Researcher.")
    
    # Return only the fields we want to update
    return {
        "manager_messages": [manager_message]
    }

def run_researcher(state: Dict[str, Any]) -> Dict[str, Any]:
    print("🔬 Researcher Agent: Starting research...")

    destination = state.get("destination", "Paris")
    current_location = state.get("current_location", "Barcelona")
    start_date = state.get("start_date", "2025-09-15")
    return_date = state.get("return_date", "2025-09-20")

    research_results = {}

    print("- Finding flight prices...")
    
    source_code = get_city_code(current_location)
    dest_code = get_city_code(destination)
    
    outbound_departure_start = f"{start_date}T00:00:00"
    outbound_departure_end = f"{start_date}T23:59:59"
    inbound_departure_start = f"{return_date}T00:00:00"
    inbound_departure_end = f"{return_date}T23:59:59"

    try:
        flights = get_flight_prices.invoke({
            "source": source_code,
            "destination": dest_code,
            "outboundDepartureDateStart": outbound_departure_start,
            "outboundDepartureDateEnd": outbound_departure_end,
            "inboundDepartureDateStart": inbound_departure_start,
            "inboundDepartureDateEnd": inbound_departure_end,
            "adults": 1,
            "currency": "USD",
            "limit": 10
        })
        research_results["flights"] = flights.get('flights', [])
        print(f" - get_flight_prices returned {len(research_results['flights'])} itineraries")
    except Exception as e:
        print(f"Error fetching flight prices: {e}")
        research_results["flights"] = []

    print("- Finding hotel prices...")
    try:
        # Pass the string dates directly to the tool
        hotels_list = hotel_search.invoke({
            "query": destination,
            "gl": "us",
            "hl": "en",
            'currency': "USD",
            "check_in_date": start_date,
            "check_out_date": return_date,
            "adults": 1,
            "children": 0,
        }).get('hotels', [])

        # Manually construct the full HotelSearchResult object to satisfy the Pydantic model
        research_results["accommodations"] = {
            "query": destination,
            "check_in_date": start_date,
            "check_out_date": return_date,
            "total_found": len(hotels_list),
            "hotels": hotels_list
        }
        
        print(f"    - hotel_search returned {len(hotels_list)} hotels")
    except Exception as e:
        print(f"Error fetching hotel prices: {e}")
        research_results["accommodations"] = {
            "query": destination,
            "check_in_date": start_date,
            "check_out_date": return_date,
            "total_found": 0,
            "hotels": []
        }

    print("- Getting destination information...")
    try:
        destination_query = f"best things to do in {destination} attractions activities restaurants"
        destination_info = get_destination_info.invoke({
            "query": destination_query,
            "num_results": 3
        })
        
        # Parse the JSON string returned by the tool
        if isinstance(destination_info, str):
            import json
            try:
                destination_info = json.loads(destination_info)
            except json.JSONDecodeError:
                destination_info = {"error": "Failed to parse destination info"}
        
        research_results["destination_info"] = destination_info
        print(f"    - get_destination_info returned info from {len(destination_info) if isinstance(destination_info, list) else 1} sources")
    except Exception as e:
        print(f"Error fetching destination info: {e}")
        research_results["destination_info"] = {"error": str(e)}

    # Return only the fields we want to update
    return {
        "research_results": research_results,
        "researcher_messages": ["content='Research complete. Found flight, hotel, and destination information.'"]
    }

def run_calculator(state: Dict[str, Any]) -> Dict[str, Any]:
    print("💵 Calculator Agent: Starting...")

    flights = state["research_results"].get("flights", [])
    accommodations = state["research_results"].get("accommodations", {}).get("hotels", [])
    
    flight_prices = [
        flight.get('priceUSD', 0) for flight in flights
    ]
    hotel_prices = [
        hotel.get('price', {}).get('per_night_value', 0) for hotel in accommodations
    ]

    start_date = state.get("start_date", "2025-09-15")
    return_date = state.get("return_date", "2025-09-20")
    
    if start_date and return_date:
        days = (datetime.strptime(return_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
    else:
        days = 0

    calculator_results = {}
    try:
        quotation = make_quotation.invoke({
            "flight_prices": flight_prices,
            "hotel_prices": hotel_prices,
            "days": days,
            "start_date": start_date,
            "end_date": return_date,
            "destination": state.get("destination", "Paris")
        })
        calculator_results = quotation
        print(f"    - make_quotation returned: {json.dumps(quotation, indent=2)}")
    except Exception as e:
        print(f"Error making quotation: {e}")
        calculator_results = {}

    # Return only the fields we want to update
    return {
        "calculator_results": calculator_results,
        "calculator_messages": [f"content='Cost calculation complete. Total cost: {calculator_results.get('final_quotation', 'N/A')}'"]
    }

def run_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    print("📅 Planner Agent: Starting to plan...")

    destination = state.get("destination", "Paris")
    start_date = state.get("start_date", "2025-09-15")
    return_date = state.get("return_date", "2025-09-20")
    
    planner_results = {}

    print("- Getting weather forecast...")
    try:
        weather_forecast = get_weather_forecast.invoke({
            "location": destination,
            "days": 5
        })
        planner_results["weather_forecast"] = weather_forecast
        print(f"    - get_weather_forecast returned a forecast for {len(weather_forecast.get('forecasts', []))} days")
    except Exception as e:
        print(f"Error fetching weather forecast: {e}")
        planner_results["weather_forecast"] = {"human_readable_summary": "Weather information not available.", "forecasts": []}

    print("- Finding local events...")
    try:
        events = search_events.invoke({
            "location": destination,
            "start_date": start_date,
            "end_date": return_date
        })
        planner_results["local_events"] = events
        print(f"    - search_events returned {len(events)} events")
    except Exception as e:
        print(f"Error searching for events: {e}")
        planner_results["local_events"] = []

    # Return only the fields we want to update
    return {
        "planner_results": planner_results,
        "planner_messages": ["content='Planning complete. Found weather and events.'"]
    }
    
def run_merge_results(state: Dict[str, Any]) -> Dict[str, Any]:
    print("🤝 Merging results from Calculator and Planner...")
    # This node doesn't need to update anything, just acts as a synchronization point
    return {}

def run_summarizer(state: Dict[str, Any]) -> Dict[str, Any]:
    print("📝 Summarizer Agent: Starting...")
    
    quotation = state.get("calculator_results", {})
    itinerary = state.get("planner_results", {})
    research_results = state.get("research_results", {})
    
    # Ensure all are dicts
    if not isinstance(quotation, dict):
        quotation = {}
    if not isinstance(itinerary, dict):
        itinerary = {}
    if not isinstance(research_results, dict):
        research_results = {}
    
    destination = state.get('destination', 'Unknown Destination')
    travel_dates = state.get('travel_dates', 'N/A')
    
    # Build comprehensive final vacation plan
    final_plan_parts = [
        f"# 🌍 Final Vacation Plan: {destination}",
        f"**Travel Dates:** {travel_dates}",
        "",
        "## ✈️ Recommended Flights",
    ]
    
    # Flight recommendations
    flights = research_results.get("flights", [])
    if flights:
        best_flight = flights[0]  # Assume first is best
        airline = best_flight.get("airline", "N/A")
        price = best_flight.get("priceUSD", 0)
        duration = best_flight.get("durationOutbound", "N/A")
        final_plan_parts.extend([
            f"**Top Choice:** {airline} - ${price:.2f}",
            f"- Duration: {duration}",
            f"- Departure: {best_flight.get('departureTime', 'N/A')}",
            f"- Arrival: {best_flight.get('arrivalTime', 'N/A')}",
            ""
        ])
    else:
        final_plan_parts.append("- Flight options available in detailed report")
        final_plan_parts.append("")
    
    # Hotel recommendations
    final_plan_parts.extend([
        "## 🏨 Recommended Hotels",
        ""
    ])
    
    accommodations = research_results.get("accommodations", {})
    hotels = accommodations.get("hotels", []) if isinstance(accommodations, dict) else []
    if hotels:
        best_hotel = hotels[0]  # Assume first is best
        name = best_hotel.get("name", "N/A")
        price = best_hotel.get("price", {})
        per_night = price.get("per_night", "N/A") if isinstance(price, dict) else "N/A"
        rating = best_hotel.get("rating", "N/A")
        address_info = best_hotel.get("address", {})
        formatted_address = address_info.get("formatted", "Address not available") if isinstance(address_info, dict) else "Address not available"
        
        final_plan_parts.extend([
            f"**Top Choice:** {name}",
            f"- Price: {per_night} per night",
            f"- Rating: {rating}★" if rating != "N/A" else f"- Rating: {rating}",
            f"- Address: {formatted_address}",
            f"- Amenities: {best_hotel.get('amenities', 'Standard amenities')}",
            ""
        ])
    else:
        final_plan_parts.append("- Hotel options available in detailed report")
        final_plan_parts.append("")
    
    # Key events
    final_plan_parts.extend([
        "## 🎉 Key Events & Activities",
        ""
    ])
    
    events = itinerary.get("local_events", [])
    if events and isinstance(events, list):
        top_events = events[:3]  # Top 3 events
        for i, event in enumerate(top_events, 1):
            if isinstance(event, dict):
                title = event.get('title', 'N/A')
                venue = event.get('venue', 'N/A')
                date = event.get('formatted_date', 'N/A')
                final_plan_parts.append(f"{i}. **{title}** at {venue} ({date})")
        final_plan_parts.append("")
    else:
        final_plan_parts.append("- Local events and activities available during your stay")
        final_plan_parts.append("")
    
    # Must-see attractions
    final_plan_parts.extend([
        "## 🌍 Must-See Attractions",
        ""
    ])
    
    # Extract attractions from destination_info research
    destination_info = research_results.get("destination_info", [])
    attractions_found = False
    
    if isinstance(destination_info, list) and destination_info:
        # Try to extract attraction information from the researched content
        for source in destination_info:
            if isinstance(source, dict) and "content" in source:
                content = source.get("content", "")
                if content and len(content) > 100:  # Has substantial content
                    # Parse attractions from the content instead of showing raw HTML
                    import re
                    
                    # Extract attraction names from various patterns
                    attraction_patterns = [
                        r'(?:St\.|Saint)\s+[A-Z][a-zA-Z\s]+(?:Cathedral|Church)',  # Churches/Cathedrals
                        r'[A-Z][a-zA-Z\s]+(?:Museum|Gallery)',  # Museums
                        r'[A-Z][a-zA-Z\s]+(?:Boulevard|Street|Square)',  # Streets/Squares
                        r'[A-Z][a-zA-Z\s]+(?:Monastery|Fortress|Palace)',  # Historic sites
                        r'Mount\s+[A-Z][a-zA-Z]+',  # Mountains
                        r'[A-Z][a-zA-Z\s]+(?:Park|Garden)',  # Parks
                    ]
                    
                    found_attractions = []
                    for pattern in attraction_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches[:3]:  # Limit to 3 per pattern
                            if match not in found_attractions and len(match) > 5:
                                found_attractions.append(match.strip())
                    
                    if found_attractions:
                        final_plan_parts.append(f"**Top attractions in {destination}:**")
                        final_plan_parts.append("")
                        for i, attraction in enumerate(found_attractions[:8], 1):  # Top 8 attractions
                            final_plan_parts.append(f"{i}. {attraction}")
                        final_plan_parts.append("")
                        attractions_found = True
                        break
    
    if not attractions_found:
        # Fallback attractions based on destination
        if destination.lower() in ['paris', 'paris france']:
            attractions = [
                "Eiffel Tower – Iconic symbol of Paris",
                "Louvre Museum – Home to the Mona Lisa",
                "Arc de Triomphe – Magnificent triumphal arch",
                "Notre-Dame Cathedral – Gothic masterpiece",
                "Champs-Élysées – Famous shopping avenue"
            ]
        elif destination.lower() in ['sofia', 'sofia bulgaria']:
            attractions = [
                "Alexander Nevsky Cathedral – Stunning Orthodox cathedral",
                "Vitosha Boulevard – Main shopping and dining street",
                "National Palace of Culture – Cultural and congress center",
                "Boyana Church – UNESCO World Heritage medieval church",
                "Sofia Central Market Hall – Historic covered market",
                "Mount Vitosha – Mountain park for hiking and skiing",
                "Ivan Vazov National Theatre – Historic neoclassical theater",
                "Serdica Archaeological Complex – Ancient Roman ruins"
            ]
        else:
            attractions = [
                f"Historic center of {destination}",
                f"Main cultural attractions",
                f"Local museums and galleries",
                f"Traditional markets and shopping areas",
                f"Scenic viewpoints and parks"
            ]
        
        for attraction in attractions:
            final_plan_parts.append(f"- {attraction}")
    
    final_plan_parts.append("")
    
    # Weather summary
    weather = itinerary.get("weather_forecast", {})
    if weather and isinstance(weather, dict) and weather.get("human_readable_summary"):
        final_plan_parts.extend([
            "## 🌤️ Weather Outlook",
            "",
            weather["human_readable_summary"][:300] + "...",
            ""
        ])
    
    # Cost summary
    final_plan_parts.extend([
        "## 💰 Cost Summary",
        "",
        f"- **Flight Cost:** {format_currency(quotation.get('flight_total', 0), 'USD')}",
        f"- **Hotel Cost:** {format_currency(quotation.get('hotel_total', 0), 'USD')}",
        f"- **Daily Expenses:** {format_currency(quotation.get('daily_cost_estimate', 120), 'USD')} per day",
        f"- **Total Trip Cost:** {format_currency(quotation.get('final_quotation', 0), 'USD')}",
        ""
    ])
    
    # Final recommendation
    final_plan_parts.extend([
        "## ✅ Summary Recommendation",
        "",
        f"Your {quotation.get('days', 5)}-day trip to {destination} promises to be an amazing experience! ",
        f"With a total budget of {format_currency(quotation.get('final_quotation', 0), 'USD')}, you'll enjoy ",
        f"comfortable accommodations, convenient flights, and access to the city's top attractions and events. ",
        f"The weather looks favorable for sightseeing and outdoor activities. ",
        f"Book your flights and hotels early for the best rates, and don't forget to check local event schedules closer to your travel dates.",
        "",
        "**Have a wonderful trip! 🎉**"
    ])
    
    final_plan = "\n".join(final_plan_parts)
    
    print("    - Generated comprehensive final plan. Length:", len(final_plan))
    
    # Return only the fields we want to update
    return {
        "final_plan": final_plan,
        "summarizer_messages": [final_plan]
    }
    
# Node factory functions for LangGraph
def make_researcher_node(llm, tools, prompt_cfg):
    return RunnableLambda(run_researcher)

def make_calculator_node(llm, tools, prompt_cfg):
    return RunnableLambda(run_calculator)

def make_planner_node(llm, tools, prompt_cfg):
    return RunnableLambda(run_planner)

def make_merge_node(llm, tools, prompt_cfg):
    return RunnableLambda(run_merge_results)

def make_summarizer_node(llm, tools, prompt_cfg):
    return RunnableLambda(run_summarizer)

def make_manager_node(llm, prompt_cfg):
    return RunnableLambda(run_manager)
