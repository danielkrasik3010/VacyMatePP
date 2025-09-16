import sys
import os
import logging
from typing import TypedDict, Optional, Dict, Any
from pydantic import BaseModel
from langchain_core.runnables import Runnable, RunnableLambda
from langgraph.graph import StateGraph, START, END

# Ensure current directory and parent are discoverable when running directly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the main state object and components
from states.VacayMate_state import VacationPlannerState, initialize_vacation_state
from graphs.VacayMate_graph import build_vacation_graph
from consts import (
    MANAGER,
    RESEARCHER,
    CALCULATOR,
    PLANNER,
    SUMMARIZER,
    MERGE_RESULTS,
)

# Configuration dictionary
config = {
    'vacaymate_system': {
        'max_retries': 3,
        'timeout_seconds': 300,
        'max_search_queries': 5,
        'max_hotels': 10,
        'max_events': 10,
        'agents': {
            'manager': {
                'llm': 'gpt-4o-mini',
                'prompt_config': {
                    'role': 'Vacation Manager & Orchestrator',
                    'instruction': """You are the central manager of the VacayMate system.
Your job is to:
1. Receive user input (current location, vacation destination, date range).
2. Validate the input and extract structured details.
3. Route tasks to the appropriate agents (Researcher, Calculator, Planner, Summarizer).
4. Collect results and ensure workflow completes in the correct sequence.
Delegate tasks in a strict, sequential order:
1. Researcher: First, send all vacation details to the Researcher agent to gather raw data on flights, hotels, and activities.
2. Calculator: Once the Researcher completes its task, send the gathered cost data (flights, hotels) to the Calculator agent.
3. Planner: Simultaneously, send the destination, date range, and activities data to the Planner agent.
4. Summarizer: After both the Calculator and Planner have finished, send their respective outputs (the quotation and the itinerary) to the Summarizer agent for final presentation.
Never perform calculations or planning yourself — always delegate.""",
                    'output_constraints': [
                        'Return structured, validated input with keys: current_location, destination, date_range',
                        'Only delegate tasks, do not attempt to complete them'
                    ],
                    'goal': 'Orchestrate the full vacation planning workflow'
                }
            },
            'researcher': {
                'llm': 'gpt-4o-mini',
                'tools': [
                    'destination_info_tool',
                    'Flight_prices_tool',
                    'Hotel_prices_tool'
                ],
                'prompt_config': {
                    'role': 'Data Researcher for vacation planning',
                    'instruction': """Collect raw data for the given destination and date range using the available tools:
- Use the `Flight_prices_tool` to find flight options and prices.
- Use the `Hotel_prices_tool` to find hotel availability and pricing.
- Use the `destination_info_tool` to find local activities, attractions, and restaurants.
Return results in structured JSON format.""",
                    'output_constraints': [
                        'Organize data into flights, hotels, activities, and events',
                        'Ensure at least 3 options per category (if available)'
                    ],
                    'goal': 'Gather all raw data necessary for planning and cost estimation'
                }
            },
            'calculator': {
                'llm': 'gpt-4o-mini',
                'tools': [
                    'Make_quotation_tool'
                ],
                'prompt_config': {
                    'role': 'Financial Calculator',
                    'instruction': """Use the `Make_quotation_tool` to calculate the total estimated trip cost. This tool requires specific inputs: a list of hotel prices, a list of flight prices, the start and end dates of the trip, and the destination.""",
                    'output_constraints': [
                        'Provide total, per-person, and daily costs in structured format',
                        'Ensure math accuracy using the Make_quotation_tool'
                    ],
                    'goal': 'Generate a precise vacation quotation'
                }
            },
            'planner': {
                'llm': 'gpt-4o-mini',
                'tools': [
                    'Weather_Forecast_tool',
                    'Event_finder_tool'
                ],
                'prompt_config': {
                    'role': 'Itinerary Planner',
                    'instruction': """Design a day-by-day itinerary for the vacation using the activity and event data provided.
Consider:
- Location proximity (avoid unnecessary travel)
- Weather forecasts (use the `Weather_Forecast_tool`)
- Logical grouping of activities
- Variety (mix of cultural, leisure, dining, and events)
- Also, use the `Event_finder_tool` to find local events to include in the itinerary.""",
                    'output_constraints': [
                        'Provide a structured day-by-day itinerary',
                        'Each day must include at least one main activity and optional extras'
                    ],
                    'goal': 'Produce a realistic, enjoyable day-by-day vacation plan'
                }
            },
            'summarizer': {
                'llm': 'gpt-4o-mini',
                'prompt_config': {
                    'role': 'Vacation Summarizer & Presenter',
                    'instruction': """Combine the quotation (from Calculator) and itinerary (from Planner) into one polished output.
The output must include:
- A cost summary section
- A detailed daily itinerary section
- A friendly conclusion""",
                    'output_constraints': [
                        'Output should be user-friendly and well-formatted (Markdown or rich text)',
                        'Do not lose details from the quotation or itinerary'
                    ],
                    'goal': 'Deliver the final vacation plan in a clear and engaging way'
                }
            }
        }
    }
}

# ------------------- Vacation Planner Class -------------------

class VacayMate:
    """
    LangGraph-based vacation planning system.
    """

    def __init__(self, llm_model: str = "gpt-4o-mini") -> None:
        # Create a simple config for the graph builder
        graph_config = {
            "llm": llm_model,
            "tools": [],
            "prompt_config": {}
        }
        self.graph = build_vacation_graph(graph_config)
    
    def _get_initial_state(self) -> Dict[str, Any]:
        """
        Returns the initial state for the LangGraph.
        """
        return {
            "user_request": "",
            "current_location": "",
            "destination": "",
            "travel_dates": "",
            "start_date": "",
            "return_date": "",
            "manager_messages": [],
            "researcher_messages": [],
            "calculator_messages": [],
            "planner_messages": [],
            "summarizer_messages": [],
            "research_results": {},
            "calculator_results": {},
            "planner_results": {}
        }

    def run(self, user_request: str, current_location: str, destination: str, start_date: str, return_date: str):
        """
        Runs the VacayMate workflow with the given user input.
        """
        initial_state = initialize_vacation_state(
            user_request=user_request,
            current_location=current_location,
            destination=destination,
            start_date=start_date,
            return_date=return_date
        )
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        # Export to Markdown file
        self._export_markdown_plan(final_state, destination, start_date, return_date)
        
        return final_state
    
    def _export_markdown_plan(self, state: Dict[str, Any], destination: str, start_date: str, return_date: str):
        """Export the complete vacation plan to a Markdown file."""
        import os
        from datetime import datetime
        
        # Create outputs directory if it doesn't exist
        outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
        os.makedirs(outputs_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vacation_plan_{destination.lower()}_{timestamp}.md"
        filepath = os.path.join(outputs_dir, filename)
        
        # Build comprehensive Markdown content
        markdown_content = self._build_markdown_content(state, destination, start_date, return_date)
        
        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"\n📄 Vacation plan exported to: {filepath}")
        except Exception as e:
            print(f"\n❌ Error exporting Markdown file: {e}")
    
    def _build_markdown_content(self, state: Dict[str, Any], destination: str, start_date: str, return_date: str) -> str:
        """Build the complete Markdown content for the vacation plan."""
        from datetime import datetime
        
        lines = [
            f"# 🌍 Vacation Plan: {destination}",
            f"**Generated on:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            f"**Travel Dates:** {start_date} to {return_date}",
            "",
            "---",
            ""
        ]
        
        # Manager Section
        lines.extend([
            "## 🎬 Manager Agent Results",
            ""
        ])
        manager_messages = state.get("manager_messages", [])
        if manager_messages:
            for msg in manager_messages:
                lines.append(f"- {msg}")
        else:
            lines.append("- No manager messages available")
        lines.append("")
        
        # Researcher Section
        lines.extend([
            "## 🔬 Researcher Agent Results",
            ""
        ])
        
        research_results = state.get("research_results", {})
        
        # Flights
        lines.extend([
            "### ✈️ Flight Options",
            ""
        ])
        flights = research_results.get("flights", [])
        if flights:
            # Create flight table
            lines.extend([
                "| Airline | Flight No. | From | To | Departure | Arrival | Duration | Price |",
                "|---------|------------|------|----|-----------|---------|-----------:|-------|"
            ])
            for flight in flights[:5]:
                airline = flight.get("airline", "N/A")
                flight_num = flight.get("flightNumber", "N/A")
                from_airport = flight.get("departureAirport", "N/A")
                to_airport = flight.get("arrivalAirport", "N/A")
                departure = flight.get("departureTime", "N/A")
                arrival = flight.get("arrivalTime", "N/A")
                duration = flight.get("durationOutbound", "N/A")
                price = f"${flight.get('priceUSD', 0):.2f}"
                
                lines.append(f"| {airline} | {flight_num} | {from_airport} | {to_airport} | {departure} | {arrival} | {duration} | {price} |")
        else:
            lines.append("- No flight options found")
            
        lines.append("")
        
        # Hotels
        lines.extend([
            "### 🏨 Hotel Options",
            ""
        ])
        accommodations = research_results.get("accommodations", {})
        hotels = accommodations.get("hotels", []) if isinstance(accommodations, dict) else []
        if hotels:
            # Create hotel table
            lines.extend([
                "| Hotel | Price/Night | Rating | Address | Amenities | Link |",
                "|-------|-------------|--------|---------|-----------|------|"
            ])
            for hotel in hotels[:5]:
                name = hotel.get("name", "N/A")
                price = hotel.get("price", {})
                per_night = price.get("per_night", "N/A") if isinstance(price, dict) else "N/A"
                rating = f"{hotel.get('rating', 'N/A')}★" if hotel.get('rating') else "N/A"
                address = hotel.get("address", {})
                area = address.get("area", "N/A") if isinstance(address, dict) else "N/A"
                amenities = hotel.get("amenities", "N/A")
                booking_link = hotel.get("booking_link", "")
                link_text = "[Book](link)" if booking_link else "N/A"
                
                lines.append(f"| {name} | {per_night} | {rating} | {area} | {amenities} | {link_text} |")
        else:
            lines.append("- No hotel options found")
            
        lines.append("")
        
        # Destination Info - Parse into attractions
        dest_info = research_results.get("destination_info", [])
        if dest_info and isinstance(dest_info, list):
            lines.extend([
                "### 🗺️ Top Attractions & Highlights",
                ""
            ])
            
            # Extract and parse attractions from the content
            attractions = self._parse_attractions_from_content(dest_info, destination)
            
            if attractions:
                for i, attraction in enumerate(attractions[:15], 1):
                    lines.append(f"{i}. **{attraction['name']}** – {attraction['description']}")
            else:
                lines.extend([
                    "**Popular destinations and attractions:**",
                    f"- Explore the historic center of {destination}",
                    f"- Visit local museums and cultural sites",
                    f"- Experience the local cuisine and dining scene",
                    f"- Discover parks and outdoor attractions",
                    f"- Shop at local markets and boutiques"
                ])
            lines.append("")
        
        # Calculator Section
        lines.extend([
            "## 💵 Calculator Agent Results",
            ""
        ])
        calculator_results = state.get("calculator_results", {})
        if calculator_results:
            lines.extend([
                f"- **Days:** {calculator_results.get('days', 'N/A')}",
                f"- **Hotel Total:** ${calculator_results.get('hotel_total', 0):.2f}",
                f"- **Flight Total:** ${calculator_results.get('flight_total', 0):.2f}",
                f"- **Daily Cost Estimate:** ${calculator_results.get('daily_cost_estimate', 0):.2f}",
                f"- **Daily Total:** ${calculator_results.get('daily_total', 0):.2f}",
                f"- **Subtotal:** ${calculator_results.get('subtotal', 0):.2f}",
                f"- **Commission Rate:** {calculator_results.get('commission_rate', 0)*100:.1f}%",
                f"- **Commission Amount:** ${calculator_results.get('commission_amount', 0):.2f}",
                f"- **Final Quotation:** ${calculator_results.get('final_quotation', 0):.2f}",
                ""
            ])
        else:
            lines.append("- No calculator results available")
            
        lines.append("")
        
        # Planner Section
        lines.extend([
            "## 📅 Planner Agent Results",
            ""
        ])
        
        planner_results = state.get("planner_results", {})
        
        # Weather
        weather = planner_results.get("weather_forecast", {})
        if weather and isinstance(weather, dict):
            lines.extend([
                "### 🌤️ Weather Forecast",
                ""
            ])
            if weather.get("human_readable_summary"):
                lines.append(weather["human_readable_summary"])
                lines.append("")
            
            forecasts = weather.get("forecasts", [])
            if forecasts:
                lines.append("**Daily Forecasts:**")
                for forecast in forecasts:
                    if isinstance(forecast, dict):
                        date = forecast.get("date", "N/A")
                        condition = forecast.get("condition", "N/A")
                        temp_high = forecast.get("temp_high", "N/A")
                        temp_low = forecast.get("temp_low", "N/A")
                        lines.append(f"- **{date}:** {condition}, High: {temp_high}°, Low: {temp_low}°")
                lines.append("")
        
        # Events
        events = planner_results.get("local_events", [])
        if events and isinstance(events, list):
            lines.extend([
                "### 🎉 Local Events",
                ""
            ])
            for i, event in enumerate(events[:10], 1):
                if isinstance(event, dict):
                    title = event.get("title", "N/A")
                    venue = event.get("venue", "N/A")
                    date = event.get("formatted_date", "N/A")
                    description = event.get("description", "")
                    desc_preview = description[:150] + "..." if len(description) > 150 else description
                    lines.extend([
                        f"**{i}. {title}**",
                        f"- Venue: {venue}",
                        f"- Date: {date}",
                        f"- Description: {desc_preview}" if desc_preview else "",
                        ""
                    ])
        else:
            lines.append("- No local events found")
            
        lines.append("")
        
        # Summarizer Section - Use the comprehensive final plan
        lines.extend([
            "## 📝 Complete Vacation Plan Summary",
            ""
        ])
        
        summarizer_messages = state.get("summarizer_messages", [])
        final_plan = state.get("final_plan", "")
        
        if final_plan and isinstance(final_plan, str) and len(final_plan) > 100:
            # Use the final_plan field which contains the comprehensive plan
            lines.append(final_plan)
        elif summarizer_messages:
            # Fallback to summarizer messages
            final_summary = summarizer_messages[-1]
            if isinstance(final_summary, str) and len(final_summary) > 100:
                lines.append(final_summary)
            else:
                lines.append("- Comprehensive vacation plan generated by AI assistant")
        else:
            lines.append("- Vacation plan summary will be generated after all agents complete their tasks")
            
        lines.extend([
            "",
            "---",
            "",
            f"*Generated by VacayMate AI Travel Planning System*",
            f"*Export completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        return "\n".join(lines)
    
    def _parse_attractions_from_content(self, dest_info: list, destination: str) -> list:
        """Parse destination content to extract top attractions with descriptions."""
        attractions = []
        
        # Common Paris attractions (fallback/examples)
        paris_attractions = [
            {"name": "Eiffel Tower", "description": "Iconic iron lattice tower and symbol of Paris"},
            {"name": "Louvre Museum", "description": "World's largest art museum, home to the Mona Lisa"},
            {"name": "Notre-Dame Cathedral", "description": "Gothic masterpiece on Île de la Cité"},
            {"name": "Arc de Triomphe", "description": "Triumphal arch at the western end of Champs-Élysées"},
            {"name": "Champs-Élysées", "description": "Famous avenue for shopping and strolling"},
            {"name": "Montmartre & Sacré-Cœur", "description": "Artistic hilltop district with stunning basilica"},
            {"name": "Seine River Cruise", "description": "Scenic boat tour along the historic river"},
            {"name": "Latin Quarter", "description": "Historic area with narrow streets and cafés"},
            {"name": "Musée d'Orsay", "description": "Impressive collection of Impressionist masterpieces"},
            {"name": "Palace of Versailles", "description": "Opulent royal château and gardens (day trip)"},
            {"name": "Marais District", "description": "Trendy neighborhood with boutiques and galleries"},
            {"name": "Trocadéro Gardens", "description": "Best viewpoint for Eiffel Tower photos"}
        ]
        
        # Try to parse attractions from the actual content
        for info in dest_info:
            if isinstance(info, dict):
                content = info.get("content", "")
                if content and len(content) > 100:
                    # Simple parsing - look for common attraction patterns
                    import re
                    
                    # Look for numbered lists or bullet points with attraction names
                    attraction_patterns = [
                        r'(\d+\.)\s*([^.]+(?:Tower|Museum|Cathedral|Palace|Park|Garden|Bridge|Square|Market|Church)[^.]*)',
                        r'[-•]\s*([^.]+(?:Tower|Museum|Cathedral|Palace|Park|Garden|Bridge|Square|Market|Church)[^.]*)',
                        r'([A-Z][^.]*(?:Tower|Museum|Cathedral|Palace|Park|Garden|Bridge|Square|Market|Church)[^.]*)'
                    ]
                    
                    for pattern in attraction_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches[:5]:  # Limit to 5 per pattern
                            if isinstance(match, tuple):
                                attraction_text = match[-1].strip()
                            else:
                                attraction_text = match.strip()
                            
                            if len(attraction_text) > 10 and len(attraction_text) < 200:
                                # Split into name and description if possible
                                if '–' in attraction_text or '-' in attraction_text:
                                    parts = attraction_text.split('–' if '–' in attraction_text else '-', 1)
                                    name = parts[0].strip()
                                    desc = parts[1].strip() if len(parts) > 1 else "Popular attraction"
                                else:
                                    name = attraction_text[:50] + "..." if len(attraction_text) > 50 else attraction_text
                                    desc = "Must-visit destination"
                                
                                attractions.append({"name": name, "description": desc})
        
        # If we didn't find enough attractions from parsing, use destination-specific defaults
        if len(attractions) < 5:
            if destination.lower() in ['paris', 'paris france']:
                attractions.extend(paris_attractions[:12])
            else:
                # Generic attractions for other destinations
                generic_attractions = [
                    {"name": f"{destination} Historic Center", "description": "Explore the heart of the city"},
                    {"name": f"{destination} Main Cathedral/Church", "description": "Beautiful religious architecture"},
                    {"name": f"{destination} City Museum", "description": "Learn about local history and culture"},
                    {"name": f"{destination} Central Park/Garden", "description": "Green space for relaxation"},
                    {"name": f"{destination} Old Town", "description": "Traditional architecture and streets"},
                    {"name": f"{destination} Market Square", "description": "Local shopping and dining"},
                    {"name": f"{destination} Viewpoint/Tower", "description": "Panoramic city views"},
                    {"name": f"{destination} Art Gallery", "description": "Local and international art"},
                    {"name": f"{destination} Waterfront", "description": "Scenic walks along the water"},
                    {"name": f"{destination} Cultural Quarter", "description": "Arts, theaters, and entertainment"}
                ]
                attractions.extend(generic_attractions)
        
        # Remove duplicates and return top attractions
        seen_names = set()
        unique_attractions = []
        for attraction in attractions:
            name_key = attraction['name'].lower().strip()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_attractions.append(attraction)
        
        return unique_attractions[:15]

# ------------------- Main Execution -------------------

if __name__ == "__main__":
    print("🚀 Starting VacayMate System...")
    
    # You would need to define your LLM and tools here to run this file.
    # For now, this is a conceptual example.

    vacay_mate = VacayMate(llm_model="gpt-4o-mini")

    current_location = "Barcelona"
    destination = "Paris"
    start_date = "2025-09-15"
    return_date = "2025-09-20"

    print(f"\nUser Request Details:")
    print(f"   Current Location: {current_location}")
    print(f"   Destination: {destination}")
    print(f"   Start Date: {start_date}")
    print(f"   Return Date: {return_date}\n")
    
    try:
        final_state = vacay_mate.run(
            user_request=f"Plan a trip from {current_location} to {destination} from {start_date} to {return_date}.",
            current_location=current_location,
            destination=destination,
            start_date=start_date,
            return_date=return_date
        )
        print("\n--- Final Vacation Plan ---")
        print(final_state.get("summarizer_messages", ["No summary found."])[-1])
        print("\n--------------------------")
    except Exception as e:
        print(f"❌ An error occurred during the planning process: {e}")
