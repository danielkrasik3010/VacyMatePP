# main.py

from typing import Any, Dict
from pprint import pprint

from graph import build_vacation_graph
from state import initialize_vacation_state
from utils import load_config
from langgraph_utils import save_graph_visualization

from consts import (
    MANAGER,
    RESEARCHER,
    CALCULATOR,
    PLANNER,
    SUMMARIZER,
)


def run_vacation_graph(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs the VacationPlanner agentic graph with the provided LLM and configurations.
    """

    # Load configurations
    vacation_config = load_config()["vacation_system"]

    # Initialize state
    initial_state = initialize_vacation_state(
        current_location=user_input["current_location"],
        destination=user_input["destination"],
        travel_dates=user_input["travel_dates"],
        manager_prompt_cfg=vacation_config["agents"][MANAGER]["prompt_config"],
        researcher_prompt_cfg=vacation_config["agents"][RESEARCHER]["prompt_config"],
        calculator_prompt_cfg=vacation_config["agents"][CALCULATOR]["prompt_config"],
        planner_prompt_cfg=vacation_config["agents"][PLANNER]["prompt_config"],
        summarizer_prompt_cfg=vacation_config["agents"][SUMMARIZER]["prompt_config"],
    )

    # Build the graph
    graph = build_vacation_graph(vacation_config)
    save_graph_visualization(graph, graph_name="vacation_system")

    # Run the graph
    final_state = graph.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    # Example input
    user_request = {
        "current_location": "New York",
        "destination": "Barcelona",
        "travel_dates": "2025-09-10 to 2025-09-20",
    }

    response = run_vacation_graph(user_request)

    print("=" * 80)
    print("🌍 VACATION PLANNER DEMO")
    print("=" * 80)
    print("Quotation:")
    pprint(response.get("quotation", {}))
    print("=" * 80)
    print("Itinerary:")
    print(response.get("itinerary_draft", "No itinerary generated"))
    print("=" * 80)
    print("Final Plan:")
    print(response.get("final_plan", "No final plan generated"))
    print("=" * 80)