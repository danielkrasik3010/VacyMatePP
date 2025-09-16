import os
from enum import Enum


# Roles
class ROLE(Enum):
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"


# AGENTS (NODES)
MANAGER = "manager"
RESEARCHER = "researcher"
CALCULATOR = "calculator"
PLANNER = "planner"
SUMMARIZER = "summarizer"
MERGE_RESULTS = "merge_results"  # Added this constant

# TOOLS
SEARCH_TOOL = "google_search_api"
TRAVEL_PRICE_TOOL = "travel_price_checker"
EVENTS_TOOL = "local_event_finder"
HOTEL_TOOL = "hotel_booking_api"
WEATHER_TOOL = "weather_api"
CALCULATOR_TOOL = "simple_calculator"

# STATE KEYS (shared memory between agents)
USER_REQUEST = "user_request"
CURRENT_LOCATION = "current_location"
DESTINATION = "destination"
TRAVEL_DATES = "travel_dates"

RESEARCH_RESULTS = "research_results"  # flights, hotels, activities
PLANNER_RESULTS = "planner_results"    # itinerary and events data
CALCULATOR_RESULTS = "calculator_results"  # financial calculations
QUOTATION = "quotation"              # cost breakdown
ITINERARY_DRAFT = "itinerary_draft"    # raw daily plan
FINAL_PLAN = "final_plan"            # polished summary

# MESSAGES (for LangSmith observability & debugging)
MANAGER_MESSAGES = "manager_messages"
RESEARCHER_MESSAGES = "researcher_messages"
CALCULATOR_MESSAGES = "calculator_messages"
PLANNER_MESSAGES = "planner_messages"
SUMMARIZER_MESSAGES = "summarizer_messages"

# CONTROL FLAGS
PLAN_APPROVED = "plan_approved"

# CONFIGURATION
MAX_RETRIES = 3
TIMEOUT_SECONDS = 300