import json
import datetime
import sys
import os
from typing import Dict, Any, Optional
from langchain_core.runnables import Runnable
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from typing_extensions import Annotated
import operator

import sys
import os
import datetime

# --- Setup logging to both console and file ---
log_dir = os.path.join(
    os.path.dirname(__file__), "..", "outputs"
)
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(
    log_dir,
    f"debug_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)

class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()  # Ensure writes appear immediately

    def flush(self):
        # Needed for compatibility with Python's print() buffering
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger(log_file)
sys.stderr = sys.stdout  # capture errors too

print(f"🔎 Logging VacayMate run to: {log_file}")

import json
import os

def save_tool_output(name, data):
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, f"{name}_output.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved {name} output to {filepath}")
    
# LangChain tool bindings
from langchain.tools import tool

# Ensure repo root is discoverable when running directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the tools to be used by the agents
from code.tools.Flights_prices_tool import get_flight_prices
from code.tools.Hotels_prices_tool import hotel_search
from code.tools.destination_info_tool import get_destination_info
from code.tools.Event_finder_tool import search_events
from code.tools.Make_quotation_tool import make_quotation
from code.tools.Weather_Forecast_tool import get_weather_forecast
from code.consts import (
    MANAGER,
    RESEARCHER,
    PLANNER,
    CALCULATOR,
    SUMMARIZER,
)


# ========================================================================
# AGENT NODES
# ========================================================================

def make_manager_node(llm_model: Runnable) -> Runnable:
    """Creates a manager agent that initiates the vacation planning process."""
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(
            "You are the VacayMate Manager. Your task is to receive the user's initial request "
            "and pass it on to the Researcher agent to begin the planning process. "
            "Do not perform any research yourself. Simply confirm the request and start the next step."
        ),
        HumanMessage(
            "The user wants to plan a trip from {current_location} to {destination} "
            "from {start_date} to {return_date}. Please proceed with the research."
        )
    ])
    
    manager_agent = prompt_template | llm_model
    return manager_agent

def make_researcher_node(llm_model: Runnable) -> Runnable:
    """
    Creates a researcher agent that finds flight, hotel, and destination info.
    This agent manually invokes the Flights_prices_tool, Hotels_prices_tool, and
    destination_info_tool.
    """
    # Bind the tools to the LLM (although they are manually invoked, this is good practice)
    researcher_agent = llm_model.bind_tools(
        [get_flight_prices, hotel_search, get_destination_info]
    )

    def run_researcher(state: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the researcher agent to get travel info."""
        print("🔍 Researcher Agent: Starting research...")

        # Extract data from state
        current_location = state.get("current_location")
        destination = state.get("destination")
        start_date_str = state.get("start_date")
        return_date_str = state.get("return_date")

        # Convert date strings to datetime.date objects (safe for tools)
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        return_date = datetime.datetime.strptime(return_date_str, "%Y-%m-%d").date()

        # Initialize results dictionary
        results: Dict[str, Any] = {}

        # Helper normalizers -------------------------------------------------
        def normalize_flights(raw: Any) -> Dict[str, Any]:
            """Normalize various possible flight tool outputs into canonical {"itineraries": [...]}."""
            # already canonical
            if isinstance(raw, dict) and isinstance(raw.get("itineraries"), list):
                return {"itineraries": raw["itineraries"]}
            # some tools return {"flights": [...]} or {"itineraries": ...}
            if isinstance(raw, dict) and isinstance(raw.get("flights"), list):
                return {"itineraries": raw["flights"]}
            # top-level list
            if isinstance(raw, list):
                return {"itineraries": raw}
            # nested candidates
            if isinstance(raw, dict):
                for candidate in ("itineraries", "results", "data", "itineraries_list"):
                    if isinstance(raw.get(candidate), list):
                        return {"itineraries": raw[candidate]}
            # if there's an inner raw_response -> itineraries
            if isinstance(raw, dict):
                inner = raw.get("raw_response") or raw.get("data")
                if isinstance(inner, dict) and isinstance(inner.get("itineraries"), list):
                    return {"itineraries": inner.get("itineraries")}
            return {"itineraries": []}

        def normalize_hotels(raw: Any) -> Dict[str, Any]:
            """Normalize hotel results to {"hotels": [...], ...}."""
            if isinstance(raw, dict) and isinstance(raw.get("hotels"), list):
                return raw
            if isinstance(raw, list):
                return {
                    "query": destination,
                    "check_in": str(start_date),
                    "check_out": str(return_date),
                    "total_found": len(raw),
                    "hotels": raw,
                }
            return {"query": destination, "check_in": str(start_date), "check_out": str(return_date), "total_found": 0, "hotels": []}

        # -------------------------------------------------------------------

        # 1. Invoke Flights_prices_tool
        print(" - Finding flight prices...")
        outbound_departure_start = f"{start_date_str}T00:00:00"
        outbound_departure_end = f"{start_date_str}T23:59:59"
        inbound_departure_start = f"{return_date_str}T00:00:00"
        inbound_departure_end = f"{return_date_str}T23:59:59"

        from code.tools.city_mapping import get_city_code
        source_code = get_city_code(current_location)
        dest_code = get_city_code(destination)

        print(f"    - Using city codes - Source: {source_code}, Destination: {dest_code}")
        print(f"    - Invoking get_flight_prices with params: source='{source_code}', destination='{dest_code}', dates='{start_date_str}' to '{return_date_str}'")

        flight_results = get_flight_prices.invoke({
            "source": source_code,
            "destination": dest_code,
            "currency": "USD",
            "outboundDepartureDateStart": outbound_departure_start,
            "outboundDepartureDateEnd": outbound_departure_end,
            "inboundDepartureDateStart": inbound_departure_start,
            "inboundDepartureDateEnd": inbound_departure_end,
            "adults": 1,
            "limit": 10,  # Request more results
        })
        save_tool_output("flights", flight_results)
        # Normalize and store
        normalized_flights = normalize_flights(flight_results)
        results["flights"] = normalized_flights
        try:
            print(f"    - get_flight_prices (normalized) itineraries: {len(normalized_flights.get('itineraries', []))}")
        except Exception:
            print("    - get_flight_prices returned non-iterable itineraries")

        # 2. Invoke Hotels_prices_tool
        print(" - Finding hotel prices...")
        print(f"    - Invoking hotel_search with params: query='{destination}', check_in_date='{start_date_str}', check_out_date='{return_date_str}'")
        hotel_results = hotel_search.invoke({
            "query": destination,
            "gl": "us",
            "hl": "en",
            "currency": "USD",
            "check_in_date": start_date,  # Pass date object
            "check_out_date": return_date,  # Pass date object
            "adults": 1,
        })
        save_tool_output("hotel", hotel_results)

        normalized_hotels = normalize_hotels(hotel_results)
        results["accommodations"] = normalized_hotels
        try:
            print(f"    - hotel_search (normalized) hotels count: {len(normalized_hotels.get('hotels', []))}")
        except Exception:
            print("    - hotel_search returned non-iterable hotels")

        # 3. Invoke destination_info_tool (optional)
        # print(" - Getting destination information...")
        # destination_info = get_destination_info.invoke({"query": f"top attractions and things to do in {destination}"})
        # results["attractions"] = destination_info

        # Return only the new results, not the whole state.
        return {
            "research_results": results,
            "researcher_messages": ["Research complete. Found flight, hotel, and destination information."],
        }
    
    return run_researcher


def make_planner_node(llm_model: Runnable) -> Runnable:
    """
    Creates a planner agent that finds local events and weather forecasts.
    This agent manually invokes the Event_Finder_tool and Weather_Forecast_tool.
    """
    planner_agent = llm_model.bind_tools(
        [search_events, get_weather_forecast]
    )
    
    def run_planner(state: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the planner agent to get weather and local events, with normalization."""
        import json
        print("🗓️ Planner Agent: Starting to plan...")

        destination = state.get("destination")
        start_date_str = state.get("start_date")
        return_date_str = state.get("return_date")

        # Parse datetimes
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        return_date = datetime.datetime.strptime(return_date_str, "%Y-%m-%d").date()
        num_days = (return_date - start_date).days

        results: Dict[str, Any] = {}

        # 1. Invoke Weather_Forecast_tool
        print(" - Getting weather forecast...")
        print(f"    - Invoking get_weather_forecast with location: '{destination}' and days: {num_days}")
        weather_forecast = get_weather_forecast.invoke({
            "location": destination,
            "days": max(1, num_days),
            "units": "metric"
        })
        save_tool_output("weather_forecast", weather_forecast)


        # Normalize weather (tool sometimes returns JSON string)
        wf_norm: Dict[str, Any] = {"forecasts": [], "human_readable_summary": None}
        try:
            if isinstance(weather_forecast, str):
                wf_parsed = json.loads(weather_forecast)
            else:
                wf_parsed = weather_forecast
            if isinstance(wf_parsed, dict):
                wf_norm["forecasts"] = wf_parsed.get("forecasts") if isinstance(wf_parsed.get("forecasts"), list) else []
                wf_norm["human_readable_summary"] = wf_parsed.get("human_readable_summary") or None
            else:
                wf_norm["human_readable_summary"] = str(wf_parsed)
        except Exception as e:
            print("    - Warning: failed to parse weather_forecast:", e)
            wf_norm["human_readable_summary"] = str(weather_forecast)

        results["weather_forecast"] = wf_norm
        print(f"    - get_weather_forecast returned: {len(wf_norm.get('forecasts', []))} forecasts, hr_summary present: {bool(wf_norm.get('human_readable_summary'))}")

        # 2. Invoke Event_Finder_tool
        print(" - Finding local events...")
        print(f"    - Invoking search_events with location: '{destination}', start_date: '{start_date_str}', end_date: '{return_date_str}'")
        event_results = search_events.invoke({
            "location": destination,
            "start_date": start_date_str,
            "end_date": return_date_str
        })
        save_tool_output("events", event_results)

        # Normalize events (tool sometimes returns JSON string)
        events_list = []
        try:
            if isinstance(event_results, str):
                parsed_ev = json.loads(event_results)
            else:
                parsed_ev = event_results

            if isinstance(parsed_ev, dict):
                # If the tool returned a dict with a top-level list field, try to find it
                for candidate in ("events", "results", "data", "items"):
                    if isinstance(parsed_ev.get(candidate), list):
                        parsed_ev = parsed_ev[candidate]
                        break
                # if still a dict, wrap it
                if isinstance(parsed_ev, dict):
                    parsed_ev = [parsed_ev]

            if isinstance(parsed_ev, list):
                for e in parsed_ev:
                    if not isinstance(e, dict):
                        continue
                    events_list.append({
                        "title": e.get("title") or e.get("name") or None,
                        "date": e.get("date") or e.get("dates") or {},
                        "formatted_date": e.get("formatted_date") or e.get("date", {}).get("when") or None,
                        "venue": e.get("venue") or e.get("location") or None,
                        "address": e.get("address") or None,
                        "link": e.get("link") or None,
                        "description": e.get("description") or ""
                    })
        except Exception as e:
            print("    - Warning: failed to parse event_results:", e)
            # fallback: store raw string
            events_list = []

        results["local_events"] = events_list
        print(f"    - search_events returned: {len(events_list)} normalized events")

        return {
            "planner_results": results,
            "planner_messages": ["Planning complete. Found weather and events."]
        }

    return run_planner


def make_calculator_node(llm_model: Runnable) -> Runnable:
    """
    Creates a calculator agent that generates a final quotation.
    This agent manually invokes the Make_quotation_tool.
    """
    calculator_agent = llm_model.bind_tools([make_quotation])

    def run_calculator(state: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the calculator agent to create a quotation."""
        print("💰 Calculator Agent: Calculating quotation...")

        # Extract data from state's research results
        destination = state.get("destination")
        start_date_str = state.get("start_date")
        return_date_str = state.get("return_date")

        research_results = state.get("research_results", {})
        
        # Defensive extraction of itineraries (supports multiple shapes)
        flights_container = research_results.get("flights", {})
        itineraries = []
        if isinstance(flights_container, dict):
            itineraries = flights_container.get("itineraries") or flights_container.get("flights") or []
        elif isinstance(flights_container, list):
            itineraries = flights_container

        flight_prices = [
            it.get("priceUSD") for it in itineraries if isinstance(it, dict) and it.get("priceUSD") is not None
        ]
        
        # Defensive extraction of hotels
        hotels_container = research_results.get("accommodations", {})
        hotels_list = []
        if isinstance(hotels_container, dict):
            hotels_list = hotels_container.get("hotels") or []
        elif isinstance(hotels_container, list):
            hotels_list = hotels_container

        hotel_prices = [
            (h.get("price") or {}).get("per_night_value") for h in hotels_list if isinstance(h, dict) and (h.get("price") or {}).get("per_night_value") is not None
        ]

        # Handle the case where no flight or hotel prices were found
        if not flight_prices:
            print("⚠️ No flight prices found in research results. Skipping flight costs for quotation.")
            # Set prices to a single zero to avoid errors
            flight_prices = [0]
            
        if not hotel_prices:
            print("⚠️ No hotel prices found in research results. Skipping hotel costs for quotation.")
            # Set prices to a single zero
            hotel_prices = [0]
        
        print(f"    - Invoking make_quotation with hotel_prices: {hotel_prices} and flight_prices: {flight_prices}")

        # Invoke the Make_quotation_tool
        quotation_results = make_quotation.invoke({
            "destination": destination,
            "start_date": start_date_str,
            "end_date": return_date_str,
            "hotel_prices": hotel_prices,
            "flight_prices": flight_prices,
        })
        print(f"    - make_quotation returned: {json.dumps(quotation_results, indent=2)}")

        # Return only the new results, not the whole state
        return {
            "calculator_results": {"quotation": quotation_results},
            "calculator_messages": ["Quotation complete. Final estimate calculated."],
        }

    return run_calculator


def make_summarizer_node(llm_model: Runnable) -> Runnable:
    """
    Creates a summarizer agent that generates the final vacation plan.
    It does not use any tools.
    """
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(
            "You are the final summarizer agent. Your role is to take all the information "
            "from the researcher, planner, and calculator agents and create a final, "
            "human-readable vacation plan for the user. Synthesize the findings into "
            "a clear, concise, and helpful summary. Organize the final plan into "
            "sections like 'Flights', 'Accommodations', 'Itinerary', and 'Estimated Cost'."
        ),
        HumanMessage(
            "Here is all the raw data for the vacation plan: {state_dump}. "
            "Please generate the final plan based on this data."
        )
    ])

    
    
    summarizer_agent = prompt_template | llm_model | StrOutputParser()

    def run_summarizer(state: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the summarizer to create the final output (compact payload focused on trip dates)."""
        import json
        import re
        print("📝 Summarizer Agent: Generating final report...")

        # Debug: Print the entire state to see what we're working with
        print("\n🔍 Current state structure:", json.dumps(state, indent=2, default=str)[:1000] + "...")

        # Extract basic information
        current_location = state.get("current_location", "Unknown")
        destination = state.get("destination", "Unknown")
        start_date_str = state.get("start_date")
        return_date_str = state.get("return_date")

        # Parse dates with error handling
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
            return_date = datetime.datetime.strptime(return_date_str, "%Y-%m-%d").date() if return_date_str else None
        except (ValueError, TypeError) as e:
            print(f"⚠️ Error parsing dates: {e}")
            start_date = return_date = None

        # Get results from state with proper fallbacks
        research_results = state.get("research_results", {})
        planner_results = state.get("planner_results", {})
        calculator_results = state.get("calculator_results", {})
        
        # Debug: Print available keys in state
        print("\n=== DEBUG: State Keys ===")
        print(f"Research results keys: {list(research_results.keys()) if isinstance(research_results, dict) else 'Not a dict'}")
        print(f"Planner results keys: {list(planner_results.keys()) if isinstance(planner_results, dict) else 'Not a dict'}")
        print("======================\n")

        # --- Process Flights ---
        flights_list = []
        try:
            # Try to get flights from research_results first
            if isinstance(research_results, dict):
                flights_data = research_results.get("flights", {})
                if isinstance(flights_data, dict):
                    flights_list = flights_data.get("itineraries", [])
                elif isinstance(flights_data, list):
                    flights_list = flights_data
            
            # Fallback to direct state access
            if not flights_list and "top_flights" in state:
                flights_list = state["top_flights"]
                
            if not isinstance(flights_list, list):
                flights_list = []
                
            print(f"Found {len(flights_list)} flights in the data")
            
        except Exception as e:
            print(f"⚠️ Error processing flights: {e}")
            flights_list = []
        
        # Get top 5 flights by price
        top_flights = []
        try:
            if flights_list:
                top_flights = sorted(
                    [f for f in flights_list if isinstance(f, dict)],
                    key=lambda x: float(x.get("priceUSD", x.get("price", float('inf'))))
                )[:5]
                print(f"Successfully processed {len(top_flights)} flights")
        except Exception as e:
            print(f"⚠️ Error processing flights: {e}")
            import traceback
            traceback.print_exc()
            top_flights = flights_list[:5] if isinstance(flights_list, list) else []
        
        # --- Process Hotels ---
        hotels_list = []
        try:
            # Try to get hotels from research_results first
            if isinstance(research_results, dict):
                hotels_data = research_results.get("hotels", {})
                if not hotels_data:
                    hotels_data = research_results.get("accommodations", {})
                
                if isinstance(hotels_data, dict):
                    hotels_list = hotels_data.get("hotels", [])
                elif isinstance(hotels_data, list):
                    hotels_list = hotels_data
            
            # Fallback to direct state access
            if not hotels_list and "top_hotels" in state:
                hotels_list = state["top_hotels"]
            
            if not isinstance(hotels_list, list):
                hotels_list = []
                
            print(f"Found {len(hotels_list)} hotels in the data")
            
        except Exception as e:
            print(f"⚠️ Error processing hotels: {e}")
            hotels_list = []
        
        # Get top 5 hotels by price
        def get_hotel_price(hotel):
            try:
                price_info = hotel.get("price", {})
                if isinstance(price_info, dict):
                    return float(price_info.get("per_night_value", float('inf')))
                return float('inf')
            except (ValueError, TypeError):
                return float('inf')
        
        top_hotels = sorted(
            [h for h in hotels_list if isinstance(h, dict)],
            key=get_hotel_price
        )[:5]
        
        # Format the data for the final output
        formatted_flights = []
        for flight in top_flights:
            formatted_flights.append({
                "priceUSD": flight.get("priceUSD"),
                "priceEUR": flight.get("priceEUR"),
                "summary": (
                    flight.get("human_readable_summary") or 
                    flight.get("summary") or 
                    (flight.get("outbound") or {}).get("summary") or
                    f"Flight from {current_location} to {destination}"
                ),
                "bookingUrl": flight.get("bookingUrl", "#")
            })
        
        formatted_hotels = []
        for hotel in top_hotels:
            price_info = hotel.get("price", {}) if isinstance(hotel.get("price"), dict) else {}
            formatted_hotels.append({
                "name": hotel.get("name", "Unknown Hotel"),
                "per_night": price_info.get("per_night_value"),
                "total": price_info.get("total_value"),
                "summary": hotel.get("summary") or hotel.get("description") or "No description available",
                "rating": hotel.get("rating"),
                "address": (hotel.get("address") or {}).get("formatted")
            })

        # --- Process Weather Forecast ---
        weather_summary = None
        try:
            # Try to get weather from planner_results first
            weather_data = planner_results.get("weather_forecast", {})
            
            # If weather_data is a string, try to parse it as JSON
            if isinstance(weather_data, str):
                try:
                    # Remove any extra quotes and newlines
                    weather_str = weather_data.strip().strip('"')
                    weather_data = json.loads(weather_str)
                except json.JSONDecodeError as e:
                    print(f"⚠️ Error parsing weather JSON: {e}")
                    # If it's a string but not JSON, use it as is
                    weather_summary = weather_data
            
            # Fallback to direct state access
            if not weather_summary and "weather_summary" in state:
                weather_summary = state["weather_summary"]
            
            if isinstance(weather_data, dict):
                # Try to get human-readable summary first
                weather_summary = weather_data.get("human_readable_summary")
                
                if not weather_summary:
                    forecasts = weather_data.get("forecasts", [])
                    if not forecasts:
                        forecasts = weather_data.get("list", [])
                    
                    # Filter forecasts for trip dates
                    filtered_forecasts = []
                    for forecast in forecasts:
                        try:
                            forecast_date = None
                            if "dt_txt" in forecast:
                                forecast_date = datetime.datetime.strptime(forecast["dt_txt"][:10], "%Y-%m-%d").date()
                            elif "date" in forecast and isinstance(forecast["date"], str):
                                forecast_date = datetime.datetime.strptime(forecast["date"][:10], "%Y-%m-%d").date()
                            
                            if forecast_date and start_date <= forecast_date <= return_date:
                                filtered_forecasts.append(forecast)
                        except (ValueError, TypeError, KeyError) as e:
                            print(f"⚠️ Warning processing forecast date: {e}")
                            continue
                    
                    # Create weather summary
                    if filtered_forecasts:
                        weather_summary = []
                        for forecast in filtered_forecasts:
                            date_str = forecast.get("dt_txt", forecast.get("date", ""))[:10]
                            temp = forecast.get("main", {}).get("temp")
                            if temp is None:
                                temp = forecast.get("temp", {})
                                if isinstance(temp, dict):
                                    temp = temp.get("day")
                            
                            description = ""
                            if "weather" in forecast and isinstance(forecast["weather"], list) and forecast["weather"]:
                                description = forecast["weather"][0].get("description", "")
                            
                            if date_str and temp is not None:
                                weather_summary.append(f"{date_str}: {temp}°C, {description}")
                        
                        if weather_summary:
                            weather_summary = "\n- " + "\n- ".join(weather_summary)
        
        except Exception as e:
            print(f"⚠️ Error processing weather data: {e}")
            import traceback
            traceback.print_exc()
            weather_summary = f"Weather information not available: {str(e)}"

        # --- Process Events ---
        events = []
        try:
            events_data = planner_results.get("local_events", [])
            if isinstance(events_data, str):
                events_data = json.loads(events_data)
            
            if isinstance(events_data, list):
                events = events_data
            elif isinstance(events_data, dict):
                events = events_data.get("events", [])
            
            # Filter and format events
            formatted_events = []
            for event in events[:8]:  # Limit to 8 events
                if not isinstance(event, dict):
                    continue
                    
                # Handle different event formats
                title = event.get("title") or event.get("name") or "Event"
                
                # Handle date formats
                date_info = ""
                if "date" in event and isinstance(event["date"], dict):
                    date_info = event["date"].get("when") or event["date"].get("start_date") or ""
                else:
                    date_info = event.get("when") or event.get("start_date") or event.get("formatted_date") or ""
                
                # Handle venue/address
                venue = ""
                if "venue" in event and isinstance(event["venue"], str):
                    venue = event["venue"]
                elif "address" in event:
                    venue = event["address"]
                elif "location" in event and isinstance(event["location"], str):
                    venue = event["location"]
                
                formatted_events.append({
                    "title": title,
                    "date": date_info,
                    "venue": venue,
                    "link": event.get("link", "#"),
                    "description": event.get("description", "")
                })
            
            events = formatted_events
                
        except Exception as e:
            print(f"⚠️ Error processing events: {e}")
            events = []

        # --- Process Quotation ---
        quotation_summary = {
            "total_cost": "Not available",
            "flight_cost": "Not available",
            "hotel_cost": "Not available",
            "daily_budget": "Not available"
        }
        
        try:
            calculator_data = calculator_results.get("quotation", {})
            if calculator_data:
                if isinstance(calculator_data, str):
                    calculator_data = json.loads(calculator_data)
                
                if isinstance(calculator_data, dict):
                    quotation_summary = {
                        "total_cost": calculator_data.get("final_quotation", "Not available"),
                        "flight_cost": calculator_data.get("flight_total", "Not available"),
                        "hotel_cost": calculator_data.get("hotel_total", "Not available"),
                        "daily_budget": calculator_data.get("daily_cost_estimate", "Not available"),
                        "subtotal": calculator_data.get("subtotal", "Not available"),
                        "commission": calculator_data.get("commission_amount", "Not available"),
                        "days": calculator_data.get("days", 1)
                    }
        except Exception as e:
            print(f"⚠️ Error processing quotation: {e}")

        # Get flights data
        flights_data = state.get("research_results", {}).get("flights", [])
        if isinstance(flights_data, dict):
            flights_data = flights_data.get("flights", [])
            
        top_flights = []
        for flight in flights_data[:5]:  # Get top 5 flights
            outbound = flight.get("outbound", {})
            inbound = flight.get("inbound", {})
            
            top_flights.append({
                "airline": outbound.get("carrier", "Unknown Airline"),
                "departure_time": outbound.get("departureLocalTime", "").replace("T", " ").split(".")[0],
                "arrival_time": outbound.get("arrivalLocalTime", "").replace("T", " ").split(".")[0],
                "price": f"${flight.get('priceUSD', 'N/A')}",
                "flight_number": f"{outbound.get('carrierCode', '')} {outbound.get('sourceCode', '')}-{outbound.get('destinationCode', '')}",
                "summary": flight.get("human_readable_summary", "")
            })

        # Get hotels data
        hotels_data = state.get("research_results", {}).get("hotel_search", [])
        if isinstance(hotels_data, dict):
            hotels_data = hotels_data.get("hotels", [])
        
        top_hotels = []
        for hotel in hotels_data[:5]:  # Get top 5 hotels
            price_info = hotel.get("price", {})
            address_info = hotel.get("address", {})
            
            # Format price information
            price_str = "N/A"
            if isinstance(price_info, dict):
                price_str = f"${price_info.get('total_value', 'N/A')} ({price_info.get('per_night', 'N/A')}/night)"
            
            # Format address
            address = ""
            if isinstance(address_info, dict):
                address = address_info.get("formatted", "")
            elif isinstance(address_info, str):
                address = address_info
            
            top_hotels.append({
                "name": hotel.get("name", "Unknown Hotel"),
                "price": price_str,
                "rating": str(hotel.get("rating", "N/A")) + ("★" if hotel.get("rating") else ""),
                "address": address,
                "check_in": hotel.get("check_in", "N/A"),
                "check_out": hotel.get("check_out", "N/A"),
                "description": hotel.get("description", "No description available")
            })

        # Get weather data
        weather = state.get("research_results", {}).get("weather", {})
        weather_summary = weather.get("human_readable_summary", "Weather information not available")

        # Format events for the final output
        formatted_events = []
        for event in events[:5]:  # Top 5 events
            formatted_events.append({
                "title": event.get("title", "Event"),
                "date": event.get("date", ""),
                "venue": event.get("venue", ""),
                "link": event.get("link", "#")
            })
            
        concise_state = {
            "current_location": current_location,
            "destination": destination,
            "start_date": start_date_str,
            "return_date": return_date_str,
            "top_flights": top_flights,
            "top_hotels": top_hotels,
            "weather_summary": weather_summary,
            "top_events": formatted_events,  # Use the properly formatted events
            "quotation_summary": quotation_summary,
            "itinerary_draft": state.get("itinerary_draft")
        }

        try:
            state_dump = json.dumps(concise_state, indent=2, default=str)
        except Exception as e:
            print("⚠️ Warning: json.dumps failed for concise_state:", e)
            state_dump = str(concise_state)

        print(f"    - state_dump size: {len(state_dump)} characters")
        print("    - state_dump preview (first 1200 chars):")
        print(state_dump[:1200])

        try:
            # Generate the final plan directly instead of using the summarizer agent
            final_plan = f"""
--- Final Vacation Plan ---
🌍 Trip from {current_location} to {destination}
📅 {start_date_str} to {return_date_str} ({quotation_summary.get('days', 5)} days)

✈️ Flights:
"""
            
            # Add flight details with proper formatting
            if top_flights and isinstance(top_flights, list) and len(top_flights) > 0:
                for i, flight in enumerate(top_flights[:5], 1):  # Limit to top 5 flights
                    try:
                        # Format outbound flight
                        outbound = flight.get('outbound', {})
                        inbound = flight.get('inbound', {})
                        
                        final_plan += f"{i}. ✈️ {outbound.get('carrier', 'Airline')} "
                        final_plan += f"(Outbound: {outbound.get('sourceCode', '')}→{outbound.get('destinationCode', '')})\n"
                        final_plan += f"   🛫 {outbound.get('source', '')} at {outbound.get('departureLocalTime', 'N/A')}\n"
                        final_plan += f"   🛬 {outbound.get('destination', '')} at {outbound.get('arrivalLocalTime', 'N/A')}\n"
                        # Format return flight if available
                        if inbound:
                            final_plan += f"   🔄 Return: {inbound.get('sourceCode', '')}→{inbound.get('destinationCode', '')}\n"
                            final_plan += f"   🛫 {inbound.get('source', '')} at {inbound.get('departureLocalTime', 'N/A')}\n"
                            final_plan += f"   🛬 {inbound.get('destination', '')} at {inbound.get('arrivalLocalTime', 'N/A')}\n"
                        
                        # Add price and duration
                        price = flight.get('priceUSD')
                        if price:
                            final_plan += f"   💰 Total Price: ${float(price):.2f} USD\n"
                        
                        # Add a separator between flights
                        if i < min(5, len(top_flights)):
                            final_plan += "   ──────────────────────────\n"
                    except Exception as e:
                        final_plan += f"   Error processing flight {i}: {str(e)}\n"
                        if i < min(5, len(top_flights)):
                            final_plan += "   ──────────────────────────\n"
            else:
                final_plan += "No flight information available\n"

            # Add hotel details with proper formatting
            final_plan += "\n🏨 Accommodations:\n"
            if top_hotels and isinstance(top_hotels, list) and len(top_hotels) > 0:
                for i, hotel in enumerate(top_hotels[:5], 1):  # Limit to top 5 hotels
                    try:
                        # Basic info
                        final_plan += f"{i}. {hotel.get('name', 'Hotel')}\n"
                        
                        # Rating
                        rating = hotel.get('rating')
                        if rating:
                            final_plan += f"   ⭐ {rating}/5"
                            hotel_class = hotel.get('hotel_class')
                            if hotel_class:
                                final_plan += f" | {hotel_class}"
                            final_plan += "\n"
                        
                        # Price
                        price_info = hotel.get('price', {})
                        if isinstance(price_info, dict):
                            price_night = price_info.get('per_night', 'N/A')
                            price_total = price_info.get('total', 'N/A')
                            final_plan += f"   💰 {price_night} per night | {price_total} total\n"
                        
                        # Description
                        description = hotel.get('description')
                        if description:
                            final_plan += f"   📝 {description}\n"
                        
                        # Check-in/out times
                        check_in = hotel.get('check_in')
                        check_out = hotel.get('check_out')
                        if check_in and check_out:
                            final_plan += f"   🕒 Check-in: {check_in} | Check-out: {check_out}\n"
                        
                        # Address
                        address = hotel.get('address', {})
                        if isinstance(address, dict):
                            formatted_address = address.get('formatted')
                            if formatted_address:
                                final_plan += f"   📍 {formatted_address}\n"
                        # Add a separator between hotels
                        if i < min(5, len(top_hotels)):
                            final_plan += "   ──────────────────────────\n"
                    except Exception as e:
                        final_plan += f"   Error processing hotel {i}: {str(e)}\n"
                        if i < min(5, len(top_hotels)):
                            final_plan += "   ──────────────────────────\n"
            else:
                final_plan += "No hotel information available\n"

            # Add weather forecast with proper formatting
            final_plan += "\n🌤️ Weather Forecast:\n"
            if weather_summary and isinstance(weather_summary, str):
                # If it's a human-readable summary, use it as is
                if "expect" in weather_summary.lower():
                    final_plan += weather_summary + "\n"
                # Otherwise try to parse and format the weather data
                else:
                    try:
                        import json
                        weather_data = json.loads(weather_summary)
                        forecasts = weather_data.get('forecasts', [])
                        
                        for day in forecasts:
                            date = day.get('date', 'N/A')
                            condition = day.get('condition', 'N/A').title()
                            temp_high = day.get('temp_high', 'N/A')
                            temp_low = day.get('temp_low', 'N/A')
                            precipitation = day.get('precipitation', 0)
                            
                            # Add weather emoji based on condition
                            weather_emoji = "☀️"  # default
                            if 'rain' in condition.lower():
                                weather_emoji = "🌧️"
                            elif 'cloud' in condition.lower():
                                weather_emoji = "⛅"
                            elif 'snow' in condition.lower():
                                weather_emoji = "❄️"
                            
                            final_plan += f"{weather_emoji} {date}: {condition}\n"
                            final_plan += f"   🌡️ {temp_low}°C - {temp_high}°C"
                            if float(precipitation) > 0:
                                final_plan += f" | 💧 {precipitation}mm"
                            final_plan += "\n"
                    except Exception as e:
                        final_plan += f"{weather_summary}\n"
                        final_plan += f"(Error formatting weather: {str(e)})\n"
            else:
                final_plan += "Weather forecast not available\n"

            # Add events with proper formatting
            final_plan += "\n🎭 Events & Activities:\n"
            if formatted_events and isinstance(formatted_events, list) and len(formatted_events) > 0:
                for i, event in enumerate(formatted_events[:5], 1):  # Limit to top 5 events
                    try:
                        if isinstance(event, str):
                            # If it's already a formatted string, use as is
                            final_plan += f"{i}. {event}\n"
                        elif isinstance(event, dict):
                            # If it's a dictionary, format it nicely
                            title = event.get('title', 'Event')
                            date_info = event.get('date', {})
                            when = date_info.get('when', '') if isinstance(date_info, dict) else ''
                            venue = event.get('venue', event.get('address', [''])[0] if isinstance(event.get('address'), list) else '')
                            
                            final_plan += f"{i}. 🎫 {title}\n"
                            if when:
                                final_plan += f"   📅 {when}\n"
                            if venue:
                                if isinstance(venue, list):
                                    venue = ', '.join([v for v in venue if v])
                                final_plan += f"   📍 {venue}\n"
                            # Add a separator between events
                            if i < min(5, len(formatted_events)):
                                final_plan += "   ──────────────────────────\n"
                    except Exception as e:
                        final_plan += f"   Error processing event {i}: {str(e)}\n"
                        if i < min(5, len(formatted_events)):
                            final_plan += "   ──────────────────────────\n"
            else:
                final_plan += "No events information available\n"
            # Add cost summary
            if quotation_summary:
                final_plan += f"\n💰 Estimated Costs (in USD):"
                final_plan += f"\n   Flights: ${quotation_summary.get('flight_cost', 'N/A')}"
                final_plan += f"\n   Hotel: ${quotation_summary.get('hotel_cost', 'N/A')} for {quotation_summary.get('days', 1)} nights"
                final_plan += f"\n   Daily Expenses: ${quotation_summary.get('daily_budget', 'N/A')}/day"
                final_plan += f"\n   Subtotal: ${quotation_summary.get('subtotal', 'N/A')}"
                final_plan += f"\n   Commission (10%): ${quotation_summary.get('commission', 'N/A')}"
                final_plan += f"\n   \033[1mTotal Estimated Cost: ${quotation_summary.get('total_cost', 'N/A')}\033[0m\n"

            print("    - Generated final plan. Length:", len(final_plan))
            return {"final_plan": final_plan, "summarizer_messages": ["Successfully generated vacation plan."]}
            
        except Exception as e:
            err_msg = f"Summarizer failed with exception: {type(e).__name__}: {e}"
            print("❌", err_msg)
            quick_summary = (
                f"Quick fallback summary:\n"
                f"- From {current_location} to {destination}\n"
                f"- Dates: {start_date_str} to {return_date_str}\n"
                f"- Flights found: {len(top_flights) if top_flights else 0} options\n"
                f"- Hotels found: {len(top_hotels) if top_hotels else 0} options\n"
                f"- Events found: {len(formatted_events) if formatted_events else 0} options\n"
                f"- Quotation: {quotation_summary}\n"
                f"- Weather: {weather_summary[:100]}...\n"
            )
            return {"final_plan": quick_summary, "summarizer_messages": [err_msg, "Returned fallback summary."]}
    
    return run_summarizer

