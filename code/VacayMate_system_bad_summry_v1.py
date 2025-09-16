import sys
import os
from typing import TypedDict, Optional
from typing import Dict
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph, END

# Ensure repo root is discoverable when running directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Package-style imports
from code.states.VacayMate_state import VacationPlannerState
from code.llm import get_llm
from code.tools.Flights_prices_tool import get_flight_prices
from code.tools.Hotels_prices_tool import hotel_search
from code.tools.destination_info_tool import get_destination_info
from code.tools.Event_finder_tool import search_events
from code.tools.Make_quotation_tool import make_quotation
from code.tools.Weather_Forecast_tool import get_weather_forecast
from code.nodes.VacayMate_nodes import (
    make_manager_node,
    make_researcher_node,
    make_calculator_node,
    make_planner_node,
    make_summarizer_node,
)


# ------------------- Vacation Planner Class -------------------

class VacayMate:
    """
    LangGraph-based vacation planning system.
    """

    def __init__(self, llm_model: str = "gpt-4o-mini") -> None:
        # Get the actual LLM object from the string model name
        self.llm_model = get_llm(llm_model)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Builds the LangGraph for the vacation planner agent system.
        """
        workflow = StateGraph(VacationPlannerState)

        # Initialize nodes with the LLM model
        manager_node = make_manager_node(self.llm_model)
        researcher_node = make_researcher_node(self.llm_model)
        calculator_node = make_calculator_node(self.llm_model)
        planner_node = make_planner_node(self.llm_model)
        summarizer_node = make_summarizer_node(self.llm_model)

        # Add nodes to the graph
        workflow.add_node("manager", manager_node)
        workflow.add_node("researcher", researcher_node)
        workflow.add_node("calculator", calculator_node)
        workflow.add_node("planner", planner_node)
        workflow.add_node("summarizer", summarizer_node)

        # Graph structure
        workflow.set_entry_point("manager")
        workflow.add_edge("manager", "researcher")
        workflow.add_edge("researcher", "calculator")
        workflow.add_edge("researcher", "planner")
        workflow.add_edge("calculator", "summarizer")
        workflow.add_edge("planner", "summarizer")
        workflow.add_edge("summarizer", END)

        return workflow.compile()

    def run(self, current_location: str, destination: str, start_date: str, return_date: str) -> str:
        """
        Executes the vacation planning graph for a user request.
        """
        from code.states.VacayMate_state import initialize_vacation_state

        initial_state = initialize_vacation_state(
            user_request=f"Plan a trip from {current_location} to {destination} from {start_date} to {return_date}.",
            current_location=current_location,
            destination=destination,
            start_date=start_date,
            return_date=return_date,
            # no prompts provided here — nodes will add their own messages when run
        )

        final_state = self.graph.invoke(initial_state)
        return final_state["final_plan"]

# ------------------- Main Execution -------------------

if __name__ == "__main__":
    print("🚀 Starting VacayMate System...")

    vacay_mate = VacayMate(llm_model="gpt-4o-mini")

    current_location = "Barcelona"
    destination = "Paris"
    start_date = "2025-09-15"
    return_date = "2025-09-20"

    print(f"\nUser Request Details:")
    print(f"  Current Location: {current_location}")
    print(f"  Destination: {destination}")
    print(f"  Start Date: {start_date}")
    print(f"  Return Date: {return_date}\n")

    try:
        final_plan = vacay_mate.run(current_location, destination, start_date, return_date)
        print("\n--- Final Vacation Plan ---")
        print(final_plan)
        print("\n--------------------------")
    except Exception as e:
        print(f"❌ An error occurred during the planning process: {e}")
