
# state.py

from typing import List, TypedDict, Optional, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import Annotated

# ---------------- FLIGHTS ---------------- #
class FlightLeg(TypedDict):
    source: str
    sourceCode: str
    destination: str
    destinationCode: str
    departureLocalTime: str
    arrivalLocalTime: str
    carrier: str
    carrierCode: str
    cabinClass: str
    summary: str

class FlightItinerary(TypedDict):
    id: str
    priceUSD: float
    priceEUR: float
    durationOutbound: str
    durationInbound: str
    lastAvailableSeats: int
    outbound: FlightLeg
    inbound: FlightLeg
    bookingUrl: str
    human_readable_summary: str

class FlightSearchResult(TypedDict):
    itineraries: List[FlightItinerary]

# ---------------- HOTELS ---------------- #
class HotelPrice(TypedDict):
    per_night: str
    per_night_value: float
    total: str
    total_value: float

class HotelAddress(TypedDict):
    latitude: float
    longitude: float
    formatted: str

class Hotel(TypedDict):
    name: str
    description: Optional[str]
    rating: Optional[float]
    hotel_class: Optional[str]
    price: HotelPrice
    address: HotelAddress
    check_in: Optional[str]
    check_out: Optional[str]
    summary: str

class HotelSearchResult(TypedDict):
    query: str
    check_in: str
    check_out: str
    total_found: int
    hotels: List[Hotel]

# ---------------- ATTRACTIONS ---------------- #
class Attraction(TypedDict):
    name: str
    description: str
    type: str
    location: str

# ---------------- EVENTS ---------------- #
class EventDate(TypedDict):
    start_date: str
    when: str

class Event(TypedDict):
    title: str
    date: EventDate
    venue: Optional[str]
    link: str

# ---------------- WEATHER ---------------- #
class WeatherForecast(TypedDict):
    date: str
    condition: str
    temp_high: float
    temp_low: float
    wind_speed: float
    humidity: int
    precipitation: float

class WeatherForecastResult(TypedDict):
    forecasts: List[WeatherForecast]
    human_readable_summary: str

# ---------------- RESEARCH RESULTS ---------------- #
class ResearchResults(TypedDict):
    """Raw data collected by Researcher agent."""
    flights: FlightSearchResult
    accommodations: HotelSearchResult
    attractions: List[Attraction]
    tavily_research: Optional[List[Dict[str, Any]]]

# ---------------- PLANNER RESULTS ---------------- #
class PlannerResults(TypedDict):
    """Processed itinerary data from Planner agent."""
    weather_forecast: Optional[WeatherForecastResult]
    local_events: List[Event]

# ---------------- CALCULATOR RESULTS ---------------- #
class CalculatorResults(TypedDict):
    """Financial outputs from Calculator agent."""
    quotation: Dict[str, Any]

# ---------------- AGENT PROMPTS ---------------- #
class AgentPromptConfig(TypedDict):
    role: str
    instruction: str
    output_constraints: List[str]
    goal: str

# ---------------- STATE ---------------- #
class VacationPlannerState(TypedDict):
    # User input
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

    # Agent outputs
    research_results: ResearchResults
    planner_results: PlannerResults
    calculator_results: CalculatorResults

    # Prompts from config
    manager_prompt: AgentPromptConfig
    researcher_prompt: AgentPromptConfig
    calculator_prompt: AgentPromptConfig
    planner_prompt: AgentPromptConfig
    summarizer_prompt: AgentPromptConfig

    # Drafts and final outputs
    itinerary_draft: str
    final_plan: str
    plan_approved: bool

# ---------------- INITIALIZATION ---------------- #
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
    return VacationPlannerState(
        user_request=user_request,
        current_location=current_location,
        destination=destination,
        travel_dates=travel_dates,
        manager_messages=[],
        researcher_messages=[],
        calculator_messages=[],
        planner_messages=[],
        summarizer_messages=[],
        research_results={
            "flights": {},
            "accommodations": {},
            "attractions": [],
            "tavily_research": [],
        },
        planner_results={
            "weather_forecast": None,
            "local_events": [],
        },
        calculator_results={
            "quotation": {},
        },
        manager_prompt=manager_prompt_cfg,
        researcher_prompt=researcher_prompt_cfg,
        calculator_prompt=calculator_prompt_cfg,
        planner_prompt=planner_prompt_cfg,
        summarizer_prompt=summarizer_prompt_cfg,
        itinerary_draft="",
        final_plan="",
        plan_approved=False,
    )

