
# nodes.py
from typing import Any, Callable, Dict
from langchain_core.messages import HumanMessage
from llm import get_llm
from consts import *

# ---------------- MANAGER NODE ---------------- #
def make_manager_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
        # Get existing messages or initialize with user request
        messages = state.get(MANAGER_MESSAGES, [])
        
        # If no messages exist, create initial message from user request
        if not messages:
            user_request = state.get("user_request", "Plan my vacation")
            current_location = state.get("current_location", "")
            destination = state.get("destination", "")
            travel_dates = state.get("travel_dates", "")
            
            initial_message = HumanMessage(
                content=f"User Request: {user_request}\n"
                       f"Current Location: {current_location}\n"
                       f"Destination: {destination}\n"
                       f"Travel Dates: {travel_dates}\n\n"
                       f"Please validate this input and prepare to delegate tasks to the appropriate agents."
            )
            messages = [initial_message]
        
        ai_response = llm.invoke(messages)
        content = f"Manager processed input:\n\n{ai_response.content.strip()}"
        
        return {
            MANAGER_MESSAGES: [ai_response],
            "manager_brief": content,  # optional summary
        }

    return manager_node

# ---------------- RESEARCHER NODE ---------------- #
def make_researcher_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get(RESEARCHER_MESSAGES, [])
        
        # If no messages exist, create initial message from state
        if not messages:
            destination = state.get("destination", "")
            travel_dates = state.get("travel_dates", "")
            
            initial_message = HumanMessage(
                content=f"Please research the following destination and dates:\n"
                       f"Destination: {destination}\n"
                       f"Travel Dates: {travel_dates}\n\n"
                       f"Find flights, hotels, and local attractions/activities."
            )
            messages = [initial_message]
        
        ai_response = llm.invoke(messages)
        return {
            RESEARCHER_MESSAGES: [ai_response],
            RESEARCH_RESULTS: ai_response.content,  # should be structured JSON
        }

    return researcher_node

# ---------------- PLANNER NODE ---------------- #
def make_planner_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get(PLANNER_MESSAGES, [])
        
        # If no messages exist, create initial message from state
        if not messages:
            destination = state.get("destination", "")
            travel_dates = state.get("travel_dates", "")
            research_results = state.get(RESEARCH_RESULTS, {})
            
            initial_message = HumanMessage(
                content=f"Please create a day-by-day itinerary for:\n"
                       f"Destination: {destination}\n"
                       f"Travel Dates: {travel_dates}\n"
                       f"Research Results: {research_results}\n\n"
                       f"Create a detailed itinerary with activities, restaurants, and events."
            )
            messages = [initial_message]
        
        ai_response = llm.invoke(messages)
        return {
            PLANNER_MESSAGES: [ai_response],
            PLANNER_RESULTS: ai_response.content,  # structured itinerary + events
            ITINERARY_DRAFT: ai_response.content,
        }

    return planner_node

# ---------------- CALCULATOR NODE ---------------- #
def make_calculator_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def calculator_node(state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get(CALCULATOR_MESSAGES, [])
        
        # If no messages exist, create initial message from state
        if not messages:
            research_results = state.get(RESEARCH_RESULTS, {})
            travel_dates = state.get("travel_dates", "")
            destination = state.get("destination", "")
            
            initial_message = HumanMessage(
                content=f"Please calculate the total cost for this vacation:\n"
                       f"Destination: {destination}\n"
                       f"Travel Dates: {travel_dates}\n"
                       f"Research Results: {research_results}\n\n"
                       f"Calculate flights, hotels, and estimated daily expenses."
            )
            messages = [initial_message]
        
        ai_response = llm.invoke(messages)
        return {
            CALCULATOR_MESSAGES: [ai_response],
            CALCULATOR_RESULTS: ai_response.content,
            QUOTATION: ai_response.content,
        }

    return calculator_node

# ---------------- SUMMARIZER NODE ---------------- #
def make_summarizer_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def summarizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get(SUMMARIZER_MESSAGES, [])
        
        # If no messages exist, create initial message from state
        if not messages:
            quotation = state.get(QUOTATION, {})
            itinerary_draft = state.get(ITINERARY_DRAFT, "")
            
            initial_message = HumanMessage(
                content=f"Please create a final vacation plan combining:\n"
                       f"Quotation: {quotation}\n"
                       f"Itinerary Draft: {itinerary_draft}\n\n"
                       f"Create a polished, user-friendly final vacation plan."
            )
            messages = [initial_message]
        
        ai_response = llm.invoke(messages)
        return {
            SUMMARIZER_MESSAGES: [ai_response],
            FINAL_PLAN: ai_response.content,  # polished output
        }

    return summarizer_node
