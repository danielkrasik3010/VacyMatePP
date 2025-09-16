# nodes.py
import datetime
import logging
import json
from langchain_core.runnables import Runnable, RunnableLambda
from typing import Any, Callable, Dict, List
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain import hub
from llm import get_llm
from consts import *

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

def _execute_tools_from_llm_response(
    llm: Any,
    prompt: str,
    tool_map: Dict[str, Any],
    tool_call_key: str = "tool_calls"
) -> Dict[str, Any]:
    """Helper function to get tool calls from an LLM and execute them."""
    try:
        raw_response = llm.invoke(HumanMessage(content=prompt))
        tool_calls = json.loads(raw_response.content)

        results = {}
        for call in tool_calls.get(tool_call_key, []):
            tool_name = call.get("tool_name")
            tool_args = call.get("tool_args")
            
            if tool_name in tool_map:
                print(f"Calling tool: {tool_name} with args: {tool_args}")
                tool_func = tool_map[tool_name]
                # Run the tool with JSON string input, which is a common requirement.
                result = tool_func.run(json.dumps(tool_args))
                results[tool_name] = result
            else:
                logging.warning(f"Tool {tool_name} not found.")
        
        return {"results": results, "llm_response": raw_response.content}
    
    except Exception as e:
        logging.error(f"Error in tool execution helper: {str(e)}")
        return {"error": str(e), "results": {}, "llm_response": ""}

# ---------------- MANAGER NODE ---------------- #
def make_manager_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    manager_prompt_config = PROMPTS["manager"]

    def manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get(MANAGER_MESSAGES, [])
        
        if not messages:
            user_request = state.get("user_request", "Plan my vacation")
            current_location = state.get("current_location", "")
            destination = state.get("destination", "")
            travel_dates = state.get("travel_dates", "")
            
            initial_message = HumanMessage(
                content=f"""
Role: {manager_prompt_config["role"]}
Goal: {manager_prompt_config["goal"]}
Instruction: {manager_prompt_config["instruction"]}
Output Constraints: {manager_prompt_config["output_constraints"]}

User Request: {user_request}
Current Location: {current_location}
Destination: {destination}
Travel Dates: {travel_dates}
"""
            )
            messages = [initial_message]
        
        ai_response = llm.invoke(messages)
        content = f"Manager processed input:\n\n{ai_response.content.strip()}"
        
        return {
            MANAGER_MESSAGES: [ai_response],
            "manager_brief": content,
        }

    return manager_node

# ---------------- RESEARCHER NODE ---------------- #
def make_researcher_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    researcher_prompt_config = PROMPTS["researcher"]

    def researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logging.debug("Researcher node started")
        
        current_location = state.get("current_location", "paris")
        destination = state.get("destination", "munich")
        travel_dates = state.get("travel_dates", "2025-09-15 to 2025-09-20")

        all_tools = state.get("tools", [])
        
        # Safely create the tool map, checking if tools are objects or dictionaries
        tool_map = {}
        for tool in all_tools:
            tool_name = tool.name if hasattr(tool, 'name') else tool.get('name')
            if tool_name:
                tool_map[tool_name] = tool
        
        prompt = f"""
        You are a data researcher. Your task is to gather raw data for a vacation plan.

        **Trip Details:**
        - Current Location: {current_location}
        - Destination: {destination}
        - Travel Dates: {travel_dates}

        **Task:**
        Find flights, hotels, and general destination information using the available tools.
        Your final output must be a single JSON object containing a list of tool calls to make.
        Each tool call object must have `tool_name` and `tool_args`.

        **Tool List and their required arguments:**
        - `search_flights`: {{"source": "string", "destination": "string", "adults": "integer", "currency": "string", "outboundDepartureDateStart": "string", "outboundDepartureDateEnd": "string", "inboundDepartureDateStart": "string", "inboundDepartureDateEnd": "string"}}
        - `hotel_search`: {{"destination": "string", "checkin": "string", "checkout": "string"}}
        - `get_destination_info`: {{"destination": "string"}}

        **Example Output:**
        {{
          "tool_calls": [
            {{
              "tool_name": "search_flights",
              "tool_args": {{
                "source": "paris",
                "destination": "munich",
                "adults": 1,
                "currency": "EUR",
                "outboundDepartureDateStart": "2025-09-15",
                "outboundDepartureDateEnd": "2025-09-15",
                "inboundDepartureDateStart": "2025-09-20",
                "inboundDepartureDateEnd": "2025-09-20"
              }}
            }},
            {{
              "tool_name": "hotel_search",
              "tool_args": {{
                "destination": "munich",
                "checkin": "2025-09-15",
                "checkout": "2025-09-20"
              }}
            }}
          ]
        }}
        """

        results_data = _execute_tools_from_llm_response(llm, prompt, tool_map)
        
        return {
            RESEARCHER_MESSAGES: [results_data["llm_response"]],
            RESEARCH_RESULTS: results_data["results"],
            "error": results_data.get("error", None)
        }

    return researcher_node

# ---------------- CALCULATOR NODE ---------------- #
def make_calculator_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    calculator_prompt_config = PROMPTS["calculator"]

    def calculator_node(state: Dict[str, Any]) -> Dict[str, Any]:
        
        research_results = state.get(RESEARCH_RESULTS, {})
        destination = state.get("destination", "munich")
        travel_dates_str = state.get("travel_dates", "2025-09-15 to 2025-09-20")
        
        # Parse the research results to get the actual data
        try:
            # Check if the tool results exist before trying to parse them
            flights_info_str = research_results.get("search_flights", "{}")
            hotels_info_str = research_results.get("hotel_search", "{}")
            
            # The tool results are JSON strings, so we still need to parse them.
            flights_info = json.loads(flights_info_str)
            hotels_info = json.loads(hotels_info_str)
            
            flight_prices = [itinerary.get("price", 0) for itinerary in flights_info.get("itineraries", [])]
            hotel_prices = [hotel.get("price", 0) for hotel in hotels_info.get("hotels", [])]
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"Error parsing research results in calculator node: {e}")
            return {
                CALCULATOR_RESULTS: {},
                QUOTATION: {},
                "error": f"Error parsing research results: {e}"
            }
        
        all_tools = state.get("tools", [])
        tool_map = {tool.name: tool for tool in all_tools}
        
        prompt = f"""
        You are a financial calculator. Your task is to calculate the total estimated trip cost.
        
        **Trip Details:**
        - Destination: {destination}
        - Travel Dates: {travel_dates_str}
        
        **Data to Use for Calculation (these are python lists):**
        - FLIGHT PRICES: {flight_prices}
        - HOTEL PRICES: {hotel_prices}
        
        **Task:**
        Use the `make_quotation` tool to calculate the cost. Your final output must be a single JSON object containing a list of tool calls to make.
        Each tool call object must have `tool_name` and `tool_args`.

        **Tool List and their required arguments:**
        - `make_quotation`: {{"hotel_prices": "list of numbers", "flight_prices": "list of numbers", "start_date": "string", "end_date": "string", "destination": "string"}}

        **Example Output:**
        {{
          "tool_calls": [
            {{
              "tool_name": "make_quotation",
              "tool_args": {{
                "hotel_prices": [150.0, 200.0],
                "flight_prices": [500.0],
                "start_date": "2025-09-15",
                "end_date": "2025-09-20",
                "destination": "Munich"
              }}
            }}
          ]
        }}
        """

        results_data = _execute_tools_from_llm_response(llm, prompt, tool_map)
        
        return {
            CALCULATOR_RESULTS: results_data["results"],
            QUOTATION: results_data["results"].get("make_quotation", {}),
            "error": results_data.get("error", None)
        }
        
    return calculator_node

# ---------------- PLANNER NODE ---------------- #
def make_planner_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    planner_prompt_config = PROMPTS["planner"]

    def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\n=== PLANNER NODE STARTING ===")
        
        destination = state.get("destination", "munich")
        travel_dates = state.get("travel_dates", "2025-09-15 to 2025-09-20")

        all_tools = state.get("tools", [])

        # Safely create the tool map, checking if tools are objects or dictionaries
        tool_map = {}
        for tool in all_tools:
            tool_name = tool.name if hasattr(tool, 'name') else tool.get('name')
            if tool_name:
                tool_map[tool_name] = tool
        
        # Step 1: Use LLM to decide which tools to call
        tool_call_prompt = f"""
        You are an itinerary planner. Your task is to design a day-by-day itinerary.
        
        **Trip Details:**
        - Destination: {destination}
        - Travel Dates: {travel_dates}
        
        **Task:**
        Find the weather forecast and local events to include in the itinerary using your tools.
        Your final output must be a single JSON object containing a list of tool calls to make.
        Each tool call object must have `tool_name` and `tool_args`.

        **Tool List and their required arguments:**
        - `get_weather_forecast`: {{"location": "string", "days": "integer", "units": "string"}}
        - `search_events`: {{"location": "string", "start_date": "string", "end_date": "string"}}

        **Example Output:**
        {{
          "tool_calls": [
            {{
              "tool_name": "get_weather_forecast",
              "tool_args": {{
                "location": "Munich",
                "days": 5,
                "units": "metric"
              }}
            }},
            {{
              "tool_name": "search_events",
              "tool_args": {{
                "location": "Munich",
                "start_date": "2025-09-15",
                "end_date": "2025-09-20"
              }}
            }}
          ]
        }}
        """
        
        results_data = _execute_tools_from_llm_response(llm, tool_call_prompt, tool_map)
        planner_results = results_data["results"]
        
        # Step 2: Now, use the tool results to generate the actual itinerary text
        itinerary_generation_prompt = f"""
        You are an expert vacation planner. Create a day-by-day itinerary for the following trip.
        
        **Trip Details:**
        - Destination: {destination}
        - Travel Dates: {travel_dates}
        
        **Tool Results to incorporate:**
        - Weather Forecast: {planner_results.get('get_weather_forecast', 'No weather data available.')}
        - Local Events: {planner_results.get('search_events', 'No events found.')}
        
        **Instructions:**
        - Design a logical, day-by-day plan.
        - Start each day with the date and a brief overview.
        - Incorporate the weather forecast and any relevant local events you found.
        - Suggest a mix of activities, dining, and cultural experiences.
        - Ensure the itinerary is realistic and enjoyable.
        
        **Begin the itinerary now:**
        """
        
        itinerary_draft = llm.invoke(HumanMessage(content=itinerary_generation_prompt)).content
        
        print("\n=== PLANNER NODE COMPLETED ===")
        print(f"- Weather data: {'Found' if 'get_weather_forecast' in planner_results else 'Not found'}")
        print(f"- Events found: {'Found' if 'search_events' in planner_results else 'Not found'}")
        
        return {
            PLANNER_RESULTS: planner_results,
            ITINERARY_DRAFT: itinerary_draft,
            "error": results_data.get("error", None)
        }
    
    return planner_node

# ---------------- SUMMARIZER NODE ---------------- #
def make_summarizer_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    summarizer_prompt_config = PROMPTS["summarizer"]

    def summarizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get(SUMMARIZER_MESSAGES, [])
        
        if not messages:
            research_results = state.get(RESEARCH_RESULTS, {})
            planner_results = state.get(PLANNER_RESULTS, {})
            calculator_results = state.get(CALCULATOR_RESULTS, {})
            itinerary_draft = state.get(ITINERARY_DRAFT, "")
            
            research_summary = {
                "flights": research_results.get("search_flights", {}),
                "hotels": research_results.get("hotel_search", {}),
                "destination_info": research_results.get("get_destination_info", {}),
                "events": planner_results.get("search_events", {})
            }
            
            message_content = f"""
Role: {summarizer_prompt_config["role"]}
Goal: {summarizer_prompt_config["goal"]}
Instruction: {summarizer_prompt_config["instruction"]}

===== TRIP DETAILS =====
- Destination: {state.get("destination", "")}
- Travel Dates: {state.get("travel_dates", "")}
- Current Location: {state.get("current_location", "")}

===== RESEARCH SUMMARY =====
{str(research_summary)}

===== ITINERARY DRAFT =====
{itinerary_draft if itinerary_draft else "No itinerary draft available"}

===== COST ESTIMATE =====
{str(calculator_results.get("make_quotation", {}))}

Output Constraints:
{summarizer_prompt_config["output_constraints"]}
"""
            initial_message = HumanMessage(content=message_content)
            messages = [initial_message]
        
        try:
            response = llm.invoke(messages)
            
            final_plan = f"""# VACATION PLAN: {state.get('destination', 'Your Destination')}
            
## Trip Overview
- **Destination:** {state.get('destination', '')}
- **Travel Dates:** {state.get('travel_dates', '')}
- **Created on:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Plan Status:** {'Approved' if state.get('plan_approved', False) else 'Draft'}

{response.content}
"""
            
            return {
                SUMMARIZER_MESSAGES: messages + [response],
                FINAL_PLAN: final_plan,
                "plan_approved": True
            }
            
        except Exception as e:
            print(f"Error in summarizer node: {str(e)}")
            return {
                SUMMARIZER_MESSAGES: messages + [f"Error in summarizer node: {str(e)}"],
                FINAL_PLAN: "Error generating final plan. Please try again.",
                "error": str(e)
            }
    return summarizer_node
