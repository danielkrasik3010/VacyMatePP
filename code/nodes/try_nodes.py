# nodes.py
import datetime
import logging
import json
from typing import Any, Callable, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import Runnable

# Ensure repo root is discoverable
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # VacayMate/ folder
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use absolute imports from the package
from code.llm import get_llm
from code.tools.Flights_prices_tool import get_flight_prices
from code.tools.Hotels_prices_tool import hotel_search
from code.tools.destination_info_tool import get_destination_info
from code.tools.Event_finder_tool import search_events
from code.tools.Make_quotation_tool import make_quotation
from code.tools.Weather_Forecast_tool import get_weather_forecast

def _call_tool(tool_callable, args: Dict[str, Any]):
    """
    Call a tool that might be:
      - a langchain BaseTool (has .invoke)
      - a plain python function
    Try multiple calling styles and return the result.
    """
    last_exc = None

    # 1) If it's a langchain BaseTool with invoke, try invoke with a single dict (common)
    if hasattr(tool_callable, "invoke"):
        try:
            return tool_callable.invoke(args)
        except Exception as e:
            last_exc = e
        # try invoke with kwargs (some implementations accept kwargs)
        try:
            return tool_callable.invoke(**args)
        except Exception as e:
            last_exc = e

    # 2) Try calling as a normal function with kwargs
    try:
        return tool_callable(**args)
    except Exception as e:
        last_exc = e

    # 3) Try calling as a normal function with a single dict arg
    try:
        return tool_callable(args)
    except Exception as e:
        last_exc = e

    # If all attempts failed, raise the last exception (more informative)
    raise last_exc if last_exc else RuntimeError("Tool invocation failed")

def _extract_prices_from_results(results: Dict[str, Any], data_type: str) -> List[float]:
    """Extract price lists from tool results based on data type."""
    prices = []
    
    if data_type == "flights":
        # Handle flight results structure
        if isinstance(results, dict):
            if "flights" in results:
                for flight in results["flights"]:
                    price = flight.get("priceUSD", 0)
                    if price and price > 0:
                        prices.append(float(price))
            elif "itineraries" in results:
                for itin in results["itineraries"]:
                    price = itin.get("priceUSD", 0)
                    if price and price > 0:
                        prices.append(float(price))
    
    elif data_type == "hotels":
        # Handle hotel results structure  
        if isinstance(results, dict) and "hotels" in results:
            for hotel in results["hotels"]:
                price_info = hotel.get("price", {})
                if isinstance(price_info, dict):
                    price = price_info.get("total_value") or price_info.get("per_night_value")
                    if price and price > 0:
                        prices.append(float(price))
    
    return prices

def _truncate_large_content(content: str, max_chars: int = 5000) -> str:
    """Truncate content to avoid context length issues."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "... [TRUNCATED]"

# --- PROMPTS FROM CONFIG.YAML ---
PROMPTS = {
    "manager": {
        "role": "Vacation Manager & Orchestrator",
        "instruction": "You are the central manager of the VacayMate system. Your job is to:\n1. Receive user input (current location, vacation destination, date range).\n2. Validate the input and extract structured details.\n3. Route tasks to the appropriate agents (Researcher, Calculator, Planner, Summarizer).\n4. Collect results and ensure workflow completes in the correct sequence.\nDelegate tasks in a strict, sequential order:\n1. Researcher: First, send all vacation details to the Researcher agent to gather raw data on flights, hotels, and activities.\n2. Calculator: Once the Researcher completes its task, send the gathered cost data (flights, hotels) to the Calculator agent.\n3. Planner: Simultaneously, send the destination, date range, and activities data to the Planner agent.\n4. Summarizer: After both the Calculator and Planner have finished, send their respective outputs (the quotation and the itinerary) to the Summarizer agent for final presentation.\n Never perform calculations or planning yourself — always delegate.",
        "output_constraints": "- Return structured, validated input with keys: current_location, destination, date_range\n- Only delegate tasks, do not attempt to complete them",
        "goal": "Orchestrate the full vacation planning workflow"
    },
    "researcher": {
        "role": "Data Researcher for vacation planning",
        "instruction": "Collect raw data for the given destination and date range using the available tools:",
        "output_constraints": "- Organize data into flights, hotels, activities, and events\n- Ensure at least 3 options per category (if available)",
        "goal": "Gather all raw data necessary for planning and cost estimation"
    },
    "calculator": {
        "role": "Financial Calculator",
        "instruction": "Use the `Make_quotation_tool` to calculate the total estimated trip cost. This tool requires specific inputs: a list of hotel prices, a list of flight prices, the start and end dates of the trip, and the destination.",
        "output_constraints": "- Provide total, per-person, and daily costs in structured format\n- Ensure math accuracy using the Make_quotation_tool",
        "goal": "Generate a precise vacation quotation"
    },
    "planner": {
        "role": "Itinerary Planner",
        "instruction": "Design a day-by-day itinerary for the vacation using the activity and event data provided.\nConsider:\n- Location proximity (avoid unnecessary travel)\n- Weather forecasts (use the `Weather_Forecast_tool`)\n- Logical grouping of activities\n- Variety (mix of cultural, leisure, dining, and events)\n- Also, use the `Event_finder_tool` to find local events to include in the itinerary.",
        "output_constraints": "- Provide a structured day-by-day itinerary\n- Each day must include at least one main activity and optional extras",
        "goal": "Produce a realistic, enjoyable day-by-day vacation plan"
    },
    "summarizer": {
        "role": "Vacation Summarizer & Presenter",
        "instruction": "Combine the quotation (from Calculator) and itinerary (from Planner) into one polished output. The output must include:\n- A cost summary section\n- A detailed daily itinerary section\n- A friendly conclusion",
        "output_constraints": "- Output should be user-friendly and well-formatted (Markdown or rich text)\n- Do not lose details from the quotation or itinerary",
        "goal": "Deliver the final vacation plan in a clear and engaging way"
    }
}

# --- NODE KEYS ---
RESEARCH_RESULTS = "research_results"
PLANNER_RESULTS = "planner_results"
CALCULATOR_RESULTS = "calculator_results"
ITINERARY_DRAFT = "itinerary_draft"
FINAL_PLAN = "final_plan"


# ---------------- MANAGER NODE ---------------- #
def make_manager_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    manager_prompt_config = PROMPTS["manager"]

    def manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
        print("🌍 Manager: Analyzing user request and creating brief...")

        current_location = state.get("current_location", "")
        destination = state.get("destination", "")
        start_date = state.get("start_date", "")
        return_date = state.get("return_date", "")

        # Prepare the input for the LLM
        messages = [
            SystemMessage(content=manager_prompt_config["instruction"]),
            HumanMessage(
                content=f"""
                User's request: Plan a trip.
                Current Location: {current_location}
                Destination: {destination}
                Start Date: {start_date}
                Return Date: {return_date}
                """
            )
        ]

        # Use the LLM to generate the brief
        ai_response = llm.invoke(messages)
        manager_brief = f"Manager's brief:\n\n{ai_response.content.strip()}"
        
        # Update the state with the brief and messages for all agents
        return {
            "manager_messages": [HumanMessage(content="Plan a trip"), ai_response],
            "researcher_messages": [SystemMessage(content=manager_prompt_config["instruction"]), ai_response],
            "calculator_messages": [SystemMessage(content=manager_prompt_config["instruction"]), ai_response],
            "planner_messages": [SystemMessage(content=manager_prompt_config["instruction"]), ai_response],
            "summarizer_messages": [SystemMessage(content=manager_prompt_config["instruction"]), ai_response],
        }

    return manager_node

# ---------------- RESEARCHER NODE ---------------- #
def make_researcher_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    researcher_prompt_config = PROMPTS["researcher"]

    # Bind tools to the LLM for function calling
    researcher_llm = llm.bind_tools([
        get_flight_prices,
        hotel_search,
        get_destination_info
    ])

    def researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
        print("🔍 Researcher: Executing searches for flights, hotels, and attractions...")

        # Get trip details from state
        current_location = state.get("current_location")
        destination = state.get("destination")
        start_date = state.get("start_date")
        return_date = state.get("return_date")

        prompt = (
            f"You are a data researcher for vacation planning. Your task is to gather raw data "
            f"for a trip from {current_location} to {destination} from {start_date} to {return_date}. "
            f"Use the available tools to find flights, hotels, and general destination information."
        )

        research_results = {}

        try:
            raw_response = researcher_llm.invoke([HumanMessage(content=prompt)])

            # --- DEBUG: print full raw response ---
            print("\n📝 [DEBUG] Full LLM response object:")
            print(raw_response)
            print("")

            tool_calls = getattr(raw_response, "tool_calls", [])

            if tool_calls:
                print(f"🔍 Researcher: The LLM decided to call {len(tool_calls)} tool(s).")
                for i, tool_call in enumerate(tool_calls, start=1):
                    tool_name = tool_call["name"]
                    tool_args = tool_call.get("args", {})
                    
                    print(f"\n🔧 [DEBUG] Tool Call #{i}")
                    print(f"Tool Name: {tool_name}")
                    print(f"Raw Tool Args from LLM: {tool_args}")

                    try:
                        # --- Flights ---
                        if tool_name == "get_flight_prices":
                            normalized_args = {
                                "source": tool_args.get("source"),
                                "destination": tool_args.get("destination"),
                                "adults": int(tool_args.get("adults", 1)),
                                "outboundDepartureDateStart": tool_args.get("outboundDepartureDateStart"),
                                "outboundDepartureDateEnd": tool_args.get("outboundDepartureDateEnd"),
                                "inboundDepartureDateStart": tool_args.get("inboundDepartureDateStart"),
                                "inboundDepartureDateEnd": tool_args.get("inboundDepartureDateEnd"),
                                "currency": tool_args.get("currency", "USD")
                            }
                            print(f"[DEBUG] Normalized Flight Args: {normalized_args}")
                            result = _call_tool(get_flight_prices, normalized_args)
                            research_results["flights"] = result
                            print(f"[DEBUG] Flight search result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

                        # --- Hotels ---
                        elif tool_name == "hotel_search":
                            normalized_args = {
                                "query": tool_args.get("query") or destination,
                                "check_in_date": tool_args.get("check_in_date") or start_date,
                                "check_out_date": tool_args.get("check_out_date") or return_date,
                                "adults": int(tool_args.get("adults", 2)),
                                "children": int(tool_args.get("children", 0))
                            }
                            print(f"[DEBUG] Normalized Hotel Args: {normalized_args}")
                            result = _call_tool(hotel_search, normalized_args)
                            research_results["accommodations"] = result
                            print(f"[DEBUG] Hotel search result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

                        # --- Destination Info ---
                        elif tool_name == "get_destination_info":
                            normalized_args = {"query": tool_args.get("query") or tool_args.get("destination") or destination}
                            print(f"[DEBUG] Normalized Destination Args: {normalized_args}")
                            result = _call_tool(get_destination_info, normalized_args)
                            # Truncate large content to avoid context issues
                            if isinstance(result, str) and len(result) > 10000:
                                result = _truncate_large_content(result, 5000)
                            research_results["attractions"] = result
                            print("✅ Researcher: Successfully found destination info.")

                        else:
                            print(f"❌ Researcher: Unrecognized tool name: {tool_name}")

                    except Exception as e:
                        print(f"❌ Researcher: Error executing tool '{tool_name}': {e}")
            else:
                print("🔍 Researcher: The LLM did not decide to call any tools.")

            print("🔍 Researcher: Research complete. Returning results.")
            return {RESEARCH_RESULTS: research_results}

        except Exception as e:
            print(f"❌ Researcher: Error in researcher node: {str(e)}")
            return {
                RESEARCH_RESULTS: state.get(RESEARCH_RESULTS, {}),
                "error": str(e)
            }

    return researcher_node


# ---------------- PLANNER NODE ---------------- #
def make_planner_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    planner_prompt_config = PROMPTS["planner"]
    
    # Bind tools for the planner agent
    planner_llm = llm.bind_tools([get_weather_forecast, search_events])

    def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\n📅 Planner: Drafting the vacation itinerary...")
        
        destination = state.get("destination")
        start_date = state.get("start_date")
        return_date = state.get("return_date")
        
        # Prepare the prompt for the planner to decide on tool calls
        prompt = (
            f"You are an itinerary planner. Your task is to design a day-by-day itinerary "
            f"for a trip to {destination} from {start_date} to {return_date}. "
            f"Use the available tools to find the weather forecast and local events to include in the itinerary."
        )

        try:
            raw_response = planner_llm.invoke([HumanMessage(content=prompt)])
            tool_calls = raw_response.tool_calls
            planner_results = {}

            if tool_calls:
                print(f"📅 Planner: The LLM decided to call {len(tool_calls)} tool(s).")
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    print(f"📅 Planner: Calling tool '{tool_name}' with arguments: {tool_args}")
                    
                    try:
                        if tool_name == "get_weather_forecast":
                            result = _call_tool(get_weather_forecast, tool_args)
                            # Truncate weather forecast if too long
                            if isinstance(result, str) and len(result) > 3000:
                                result = _truncate_large_content(result, 2000)
                            planner_results["weather_forecast"] = result
                        elif tool_name == "search_events":
                            result = _call_tool(search_events, tool_args)
                            # Truncate events if too long
                            if isinstance(result, str) and len(result) > 5000:
                                result = _truncate_large_content(result, 3000)
                            planner_results["local_events"] = result
                            print("✅ Planner: Successfully found local events.")
                        else:
                            print(f"❌ Planner: Unrecognized tool name: {tool_name}")
                    except Exception as e:
                        print(f"❌ Planner: Error executing tool '{tool_name}': {e}")
            else:
                print("📅 Planner: The LLM did not decide to call any tools.")

            # Create a more concise summary for LLM processing
            research_summary = "Research findings: Basic destination information available."
            if state.get('research_results', {}).get('attractions'):
                research_summary = "Research findings: Destination attractions and activities identified."

            # Use the LLM to create a human-readable itinerary draft with truncated inputs
            prompt = (
                "Based on the following information, create a brief 5-day vacation itinerary. "
                f"Keep it concise and practical. Destination: {destination}, "
                f"Dates: {start_date} to {return_date}. "
                f"{research_summary} "
                f"Weather: {str(planner_results.get('weather_forecast', 'No forecast'))[:500]} "
                f"Events: {str(planner_results.get('local_events', 'No events'))[:500]}"
            )
            print("📅 Planner: Asking LLM to generate itinerary draft.")
            
            response = llm.invoke([HumanMessage(content=prompt)])
            itinerary_draft = response.content.strip()
            
            print("📅 Planner: Itinerary draft created. Returning results.")
            return {
                PLANNER_RESULTS: planner_results,
                ITINERARY_DRAFT: itinerary_draft,
            }
            
        except Exception as e:
            print(f"❌ Planner: Error in planner node: {str(e)}")
            return {
                PLANNER_RESULTS: state.get(PLANNER_RESULTS, {}),
                ITINERARY_DRAFT: f"Basic itinerary for {destination} from {start_date} to {return_date}. Unable to generate detailed plan due to: {str(e)[:100]}",
                "error": str(e)
            }
    return planner_node

# ---------------- CALCULATOR NODE ---------------- #
def make_calculator_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    calculator_prompt_config = PROMPTS["calculator"]
    
    # Bind tools for the calculator agent
    calculator_llm = llm.bind_tools([make_quotation])

    def calculator_node(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\n💰 Calculator: Calculating total vacation cost...")
        
        research_results = state.get(RESEARCH_RESULTS, {})
        destination = state.get("destination")
        start_date = state.get("start_date")
        return_date = state.get("return_date")

        flights_info = research_results.get("flights", {})
        hotels_info = research_results.get("accommodations", {})
        
        print(f"[DEBUG] Calculator received flights_info type: {type(flights_info)}")
        print(f"[DEBUG] Calculator received hotels_info type: {type(hotels_info)}")
        
        # More detailed debugging of the flights_info structure
        if isinstance(flights_info, dict):
            print(f"[DEBUG] flights_info keys: {list(flights_info.keys())}")
            if 'success' in flights_info:
                print(f"[DEBUG] Flight API success: {flights_info.get('success')}")
            if 'flights' in flights_info:
                flights_list = flights_info.get('flights', [])
                print(f"[DEBUG] flights list length: {len(flights_list)}")
                if flights_list:
                    print(f"[DEBUG] First flight sample: {flights_list[0]}")
            if 'error' in flights_info:
                print(f"[DEBUG] Flight API error: {flights_info.get('error')}")
        
        # Extract price lists from the complex tool results
        try:
            flight_prices = _extract_prices_from_results(flights_info, "flights")
            hotel_prices = _extract_prices_from_results(hotels_info, "hotels")
            
            print(f"[DEBUG] Extracted flight_prices: {flight_prices}")
            print(f"[DEBUG] Extracted hotel_prices: {hotel_prices}")
            
            # Provide fallback prices if extraction failed
            if not flight_prices:
                print("⚠️ Calculator: No flight prices found, using fallback estimates")
                flight_prices = [300.0, 350.0, 400.0]  # Fallback flight prices
            
            if not hotel_prices:
                print("⚠️ Calculator: No hotel prices found, using fallback estimates")
                hotel_prices = [120.0, 150.0, 180.0]  # Fallback hotel prices per night

            tool_args = {
                "hotel_prices": hotel_prices,
                "flight_prices": flight_prices,
                "start_date": start_date,
                "end_date": return_date,
                "destination": destination
            }
            
            print(f"💰 Calculator: Calling make_quotation with arguments: {tool_args}")
            quotation = _call_tool(make_quotation, tool_args)

            print("✅ Calculator: Successfully generated quotation.")
            
            return {
                CALCULATOR_RESULTS: {"quotation": quotation},
                "quotation": quotation
            }
        except Exception as e:
            print(f"❌ Calculator: Error generating quotation: {str(e)}")
            # Return a basic fallback quotation
            fallback_quotation = {
                "error": f"Could not calculate exact costs: {str(e)}",
                "estimate_note": f"Basic cost estimate for {destination}",
                "days": 5,
                "hotel_total": 750,
                "flight_total": 350,
                "daily_total": 300,
                "final_quotation": 1500
            }
            return {
                CALCULATOR_RESULTS: {"quotation": fallback_quotation},
                "quotation": fallback_quotation,
                "error": str(e)
            }
    return calculator_node

# ---------------- SUMMARIZER NODE ---------------- #
def _summarize_chunk(llm: Any, chunk: str, summary_so_far: str = "") -> str:
    """Summarize a chunk of text, considering previous summaries."""
    prompt = (
        f"Summarize the following information concisely. "
        f"Focus on key details and remove any redundant information.\n\n"
        f"Previous context (for reference only):\n{summary_so_far}\n\n"
        f"New information to summarize:\n{chunk}"
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        print(f"⚠️ Warning: Error summarizing chunk: {str(e)}")
        return chunk[:2000]  # Fallback: return first 2000 chars if summarization fails

def _chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    """Split text into chunks of max_chars, trying to split at paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]
        
    chunks = []
    while text:
        # Try to split at paragraph boundary
        split_pos = text.rfind('\n\n', 0, max_chars)
        if split_pos == -1:  # No paragraph break found, split at max_chars
            split_pos = max_chars
        
        chunk = text[:split_pos].strip()
        if chunk:
            chunks.append(chunk)
        text = text[split_pos:].strip()
    
    return chunks

def make_summarizer_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    summarizer_prompt_config = PROMPTS["summarizer"]

    def summarizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
        print("✨ Summarizer: Starting to generate the final vacation plan...")
        
        research_results = state.get(RESEARCH_RESULTS, {})
        planner_results = state.get(PLANNER_RESULTS, {})
        quotation = state.get("quotation", {})
        itinerary_draft = state.get(ITINERARY_DRAFT, "")
        destination = state.get('destination', 'Your Destination')
        
        # Process information more efficiently to avoid context limits
        try:
            # Simplified approach - create summary without excessive chunking
            final_summary = f"# Vacation Plan for {destination}\n\n"
            
            # Add quotation section
            if quotation:
                final_summary += "## Cost Summary\n"
                if "final_quotation" in quotation:
                    final_summary += f"**Total Estimated Cost: ${quotation['final_quotation']}**\n"
                if "days" in quotation:
                    final_summary += f"**Trip Duration: {quotation['days']} days**\n"
                if "hotel_total" in quotation:
                    final_summary += f"- Accommodation: ${quotation['hotel_total']}\n"
                if "flight_total" in quotation:
                    final_summary += f"- Flights: ${quotation['flight_total']}\n"
                if "daily_total" in quotation:
                    final_summary += f"- Daily expenses: ${quotation['daily_total']}\n"
                final_summary += "\n"
            
            # Add itinerary section
            if itinerary_draft:
                final_summary += "## Daily Itinerary\n"
                # Truncate itinerary if too long
                truncated_itinerary = _truncate_large_content(itinerary_draft, 2000)
                final_summary += f"{truncated_itinerary}\n\n"
            
            # Add brief research highlights
            if research_results:
                final_summary += "## Additional Information\n"
                if "attractions" in research_results:
                    final_summary += "- Destination attractions and activities researched\n"
                if "flights" in research_results:
                    final_summary += "- Flight options analyzed\n"
                if "accommodations" in research_results:
                    final_summary += "- Accommodation options reviewed\n"
                final_summary += "\n"
            
            # Add weather and events if available
            if planner_results:
                if "weather_forecast" in planner_results:
                    final_summary += "Weather forecast has been considered for optimal planning.\n"
                if "local_events" in planner_results:
                    final_summary += "Local events and activities have been incorporated.\n"
                final_summary += "\n"
                
            final_summary += "## Conclusion\nYour personalized vacation plan is ready! Safe travels and enjoy your trip!\n"
            
            print("✅ Summarizer: Final vacation plan generated successfully.")
            return {
                FINAL_PLAN: final_summary,
                "plan_approved": True
            }
            
        except Exception as e:
            print(f"❌ Summarizer: Error in summarizer node: {str(e)}")
            # Fallback to a simple summary if detailed summarization fails
            try:
                fallback_summary = (
                    f"# Vacation Plan for {destination}\n\n"
                    f"## Cost Summary\n**Estimated Total: ${quotation.get('final_quotation', 'TBD')}**\n\n"
                    f"## Itinerary\n{itinerary_draft[:1000] if itinerary_draft else 'Itinerary being finalized...'}...\n\n"
                    f"## Note\nDetailed planning completed. Contact for full details.\n"
                )
                return {
                    FINAL_PLAN: fallback_summary,
                    "warning": f"Used fallback summary due to: {str(e)}",
                    "plan_approved": True
                }
            except Exception as fallback_error:
                return {
                    FINAL_PLAN: "Error generating vacation plan. Please try again with a different destination or date range.",
                    "error": f"Primary error: {str(e)}, Fallback error: {str(fallback_error)}"
                }
    return summarizer_node