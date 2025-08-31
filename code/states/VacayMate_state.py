# state.py

from typing import List, TypedDict, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import Annotated

from prompt_builder import build_system_prompt_message


class VacationPlannerState(TypedDict):
    """Shared state for the VacayMate multi-agent system."""

    # User input (mandatory)
    user_request: str
    current_location: str
    destination: str
    travel_dates: str

    # Agent message histories
    manager_messages: Annotated[list[AnyMessage], add_messages]
    researcher_messages: Annotated[list[AnyMessage], add_messages]
    calculator_messages: Annotated[list[AnyMessage], add_messages]
    planner_messages: Annotated[list[AnyMessage], add_messages]
    summarizer_messages: Annotated[list[AnyMessage], add_messages]

    # Data exchanged between agents
    research_results: Dict[str, List[Dict[str, str]]]   # flights, hotels, activities
    quotation: Dict[str, float]                         # cost breakdown
    itinerary_draft: str                                # raw day-by-day plan
    final_plan: str                                     # polished summary

    # Control flags
    plan_approved: bool


def initialize_vacation_state(
    user_request: str,
    current_location: str,
    destination: str,
    travel_dates: str,
    manager_prompt_cfg: dict,
    researcher_prompt_cfg: dict,
    calculator_prompt_cfg: dict,
    planner_prompt_cfg: dict,
    summarizer_prompt_cfg: dict,
) -> VacationPlannerState:
    """Initialize the VacayMate state with default values."""

    # Manager
    manager_messages = [
        SystemMessage(build_system_prompt_message(manager_prompt_cfg)),
        HumanMessage(f"Received trip request:\n\n{user_request}"),
    ]

    # Researcher
    researcher_messages = [
        SystemMessage(build_system_prompt_message(researcher_prompt_cfg)),
        HumanMessage(f"Gather data on flights, hotels, and activities for:\n\n{user_request}"),
    ]

    # Calculator
    calculator_messages = [
        SystemMessage(build_system_prompt_message(calculator_prompt_cfg)),
        HumanMessage(f"Generate cost quotation for:\n\n{user_request}"),
    ]

    # Planner
    planner_messages = [
        SystemMessage(build_system_prompt_message(planner_prompt_cfg)),
        HumanMessage(f"Draft a daily itinerary based on research data for:\n\n{user_request}"),
    ]

    # Summarizer
    summarizer_messages = [
        SystemMessage(build_system_prompt_message(summarizer_prompt_cfg)),
        HumanMessage(f"Summarize the plan and quotation for:\n\n{user_request}"),
    ]

    return VacationPlannerState(
        user_request=user_request,
        current_location=current_location,
        destination=destination,
        travel_dates=travel_dates,
        manager_messages=manager_messages,
        researcher_messages=researcher_messages,
        calculator_messages=calculator_messages,
        planner_messages=planner_messages,
        summarizer_messages=summarizer_messages,
        research_results={},
        quotation={},
        itinerary_draft="",
        final_plan="",
        plan_approved=False,
    )
