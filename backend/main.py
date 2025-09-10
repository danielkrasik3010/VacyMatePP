"""
VacayMate Backend API
FastAPI application that wraps the VacayMate multi-agent system
"""
import sys
import os
import json
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add project root and code directory to Python path
project_root = Path(__file__).parent.parent
code_dir = project_root / 'code'

# Add to Python path if not already there
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Import FastAPI and other dependencies
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="VacayMate API", version="1.0.0")

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class TripRequest(BaseModel):
    current_location: str
    destination: str
    travel_dates: str
    startDate: str = ""
    endDate: str = ""

class FlightOption(BaseModel):
    airline: str
    departure: str
    arrival: str
    duration: str
    price: float
    stops: int

class Hotel(BaseModel):
    name: str
    rating: float
    price_per_night: float
    total_price: float
    amenities: List[str]
    description: str
    address: str

class Activity(BaseModel):
    name: str
    date: str
    time: str
    description: str
    price: Optional[float]
    location: str
    link: Optional[str]

class WeatherDay(BaseModel):
    date: str
    temperature_high: float
    temperature_low: float
    condition: str
    humidity: int
    wind_speed: float

class CostBreakdown(BaseModel):
    flights: float
    hotels: float
    activities: float
    total_before_commission: float
    commission: float
    final_total: float

class TripPlan(BaseModel):
    destination: str
    dates: str
    flights: List[FlightOption]
    hotels: List[Hotel]
    activities: List[Activity]
    weather: List[WeatherDay]
    costs: CostBreakdown
    itinerary: str
    summary: str

@app.get("/")
async def root():
    return {"message": "VacayMate API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Import the VacayMate system function
from VacayMate_system import run_vacation_graph

def parse_vacaymate_output(output_data: dict, request: TripRequest) -> TripPlan:
    """
    Parse the VacayMate system output and convert it to structured JSON format
    
    Args:
        output_data: The raw output from run_vacation_graph (should be a dict)
        request: The original TripRequest
    """
    try:
        # Ensure we have a dictionary
        if not isinstance(output_data, dict):
            if isinstance(output_data, str):
                try:
                    output_data = json.loads(output_data)
                except json.JSONDecodeError:
                    output_data = {"itinerary": output_data}
            else:
                output_data = {"itinerary": str(output_data)}
                
        data = output_data  # For backward compatibility

        # Helper function to safely get values from nested dictionaries
        def get_nested(data, *keys, default=None):
            for key in keys:
                if isinstance(data, dict):
                    data = data.get(key, {})
                else:
                    return default
            return data or default

        # Extract data with fallbacks
        flights_data = get_nested(data, "flights", default=[])
        hotels_data = get_nested(data, "hotels", default=[])
        activities_data = get_nested(data, "activities", default=[])
        weather_data = get_nested(data, "weather", default=[])
        costs_data = get_nested(data, "costs", default={})
        
        # Convert to proper types
        flights = [
            FlightOption(
                airline=flight.get("airline", "Unknown"),
                departure=flight.get("departure", ""),
                arrival=flight.get("arrival", ""),
                duration=flight.get("duration", ""),
                price=float(flight.get("price", 0.0)),
                stops=int(flight.get("stops", 0))
            )
            for flight in (flights_data if isinstance(flights_data, list) else [])
        ][:5]  # Limit to 5 flights

        hotels = [
            Hotel(
                name=hotel.get("name", "Unknown"),
                rating=float(hotel.get("rating", 0.0)),
                price_per_night=float(hotel.get("price_per_night", 0.0)),
                total_price=float(hotel.get("total_price", 0.0)),
                amenities=hotel.get("amenities", []),
                description=hotel.get("description", ""),
                address=hotel.get("address", "")
            )
            for hotel in (hotels_data if isinstance(hotels_data, list) else [])
        ][:3]  # Limit to 3 hotels

        activities = [
            Activity(
                name=activity.get("name", ""),
                date=activity.get("date", ""),
                time=activity.get("time", ""),
                description=activity.get("description", ""),
                price=float(activity.get("price", 0.0)),
                location=activity.get("location", ""),
                link=activity.get("link", "")
            )
            for activity in (activities_data if isinstance(activities_data, list) else [])
        ][:10]  # Limit to 10 activities

        weather = [
            WeatherDay(
                date=day.get("date", ""),
                temperature_high=float(day.get("temperature_high", 0.0)),
                temperature_low=float(day.get("temperature_low", 0.0)),
                condition=day.get("condition", ""),
                humidity=int(day.get("humidity", 0)),
                wind_speed=float(day.get("wind_speed", 0.0))
            )
            for day in (weather_data if isinstance(weather_data, list) else [])
        ]

        # Handle costs with defaults
        costs = CostBreakdown(
            flights=float(costs_data.get("flights", 0.0)),
            hotels=float(costs_data.get("hotels", 0.0)),
            activities=float(costs_data.get("activities", 0.0)),
            total_before_commission=float(costs_data.get("total_before_commission", 0.0)),
            commission=float(costs_data.get("commission", 0.0)),
            final_total=float(costs_data.get("final_total", 0.0))
        )

        # Handle itinerary - ensure it's a string
        itinerary = ""
        
        # First try to get the final plan or itinerary
        if 'final_plan' in data and data['final_plan']:
            if isinstance(data['final_plan'], str):
                itinerary = data['final_plan']
            else:
                itinerary = json.dumps(data['final_plan'], indent=2)
        elif 'itinerary' in data and data['itinerary']:
            if isinstance(data['itinerary'], str):
                itinerary = data['itinerary']
            else:
                itinerary = json.dumps(data['itinerary'], indent=2)
        # Check for manager messages
        elif 'manager_messages' in data and data['manager_messages']:
            # Get the last non-empty message
            for msg in reversed(data['manager_messages']):
                if not msg:
                    continue
                if isinstance(msg, dict):
                    if 'content' in msg and msg['content']:
                        itinerary = str(msg['content'])
                        break
                    else:
                        itinerary = str(msg)
                        break
                else:
                    itinerary = str(msg)
                    break
        
        # If we still don't have an itinerary, try to extract from other fields
        if not itinerary.strip():
            for key in ['research_results', 'itinerary_draft', 'output']:
                if key in data and data[key]:
                    if isinstance(data[key], str):
                        itinerary = data[key]
                    else:
                        itinerary = json.dumps(data[key], indent=2)
                    break
        
        # If all else fails, stringify the entire response
        if not itinerary.strip():
            itinerary = json.dumps(data, indent=2, default=str)
        
        # Ensure we don't exceed the max length
        if len(itinerary) > 10000:
            itinerary = itinerary[:10000] + "... [truncated]"
            
        # Limit itinerary length to prevent issues
        if len(itinerary) > 10000:  # 10k character limit
            itinerary = itinerary[:10000] + "... [truncated]"

        # Create and return the trip plan
        trip_plan = TripPlan(
            destination=request.destination,
            dates=request.travel_dates,
            flights=flights,
            hotels=hotels,
            activities=activities,
            weather=weather,
            costs=costs,
            itinerary=itinerary,
            summary=f"Vacation plan for {request.destination} from {request.travel_dates}"
        )

        return trip_plan

    except Exception as e:
        print(f"Error parsing VacayMate output: {e}")
        traceback.print_exc()
        # Return a minimal valid TripPlan with error message
        return TripPlan(
            destination=request.destination or "Unknown",
            dates=request.travel_dates or "N/A",
            flights=[],
            hotels=[],
            activities=[],
            weather=[],
            costs=CostBreakdown(
                flights=0.0,
                hotels=0.0,
                activities=0.0,
                total_before_commission=0.0,
                commission=0.0,
                final_total=0.0
            ),
            itinerary=f"Error generating trip plan: {str(e)}",
            summary="Error generating trip plan"
        )

@app.post("/plan-trip", response_model=TripPlan)
async def plan_trip(request: TripRequest):
    """
    Endpoint to plan a vacation using the VacayMate system
    """
    try:
        print(f"\n=== Received trip planning request ===")
        print(f"From: {request.current_location}")
        print(f"To: {request.destination}")
        print(f"Dates: {request.travel_dates}")
        
        # Set default dates if not provided
        start_date = request.startDate if request.startDate and request.startDate != 'undefined' else '2023-10-01'
        end_date = request.endDate if request.endDate and request.endDate != 'undefined' else '2023-10-07'
        
        # Prepare input for the vacation graph
        user_input = {
            "current_location": request.current_location,
            "destination": request.destination,
            "travel_dates": f"{start_date} to {end_date}",
            "start_date": start_date,
            "end_date": end_date,
            "user_request": f"Plan a trip from {request.current_location} to {request.destination}"
        }
        
        # Add dates to user request if they're defined
        if start_date != 'undefined' and end_date != 'undefined':
            user_input["user_request"] += f" from {start_date} to {end_date}"
        
        print("Calling run_vacation_graph with input:", json.dumps(user_input, indent=2))
        
        # Run the vacation planning graph
        result = run_vacation_graph(user_input)
        
        # Ensure we have a valid result
        if not result:
            raise ValueError("No result returned from VacayMate graph")
            
        print("\n=== Raw result from run_vacation_graph ===")
        print("Type:", type(result))
        if isinstance(result, dict):
            print("Keys:", list(result.keys()))
            if 'manager_messages' in result and isinstance(result['manager_messages'], list):
                print("Manager messages:")
                for i, msg in enumerate(result['manager_messages'][-3:], 1):  # Show last 3 messages
                    print(f"  {i}. {str(msg)[:200]}..." if len(str(msg)) > 200 else f"  {i}. {msg}")
        else:
            print("Result (first 500 chars):", str(result)[:500])
        
        print("\nParsing output...")
        
        # Parse the output
        return parse_vacaymate_output(result, request)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"\n❌ Error in plan_trip: {str(e)}")
        print(traceback.format_exc())
        # Return a minimal valid TripPlan with error message
        return TripPlan(
            destination=request.destination if hasattr(request, 'destination') else "Unknown",
            dates=getattr(request, 'travel_dates', 'N/A'),
            flights=[],
            hotels=[],
            activities=[],
            weather=[],
            costs=CostBreakdown(
                flights=0.0,
                hotels=0.0,
                activities=0.0,
                total_before_commission=0.0,
                commission=0.0,
                final_total=0.0
            ),
            itinerary=f"Error generating trip plan: {str(e)}",
            summary="Error generating trip plan"
        )

@app.get("/destinations")
async def get_popular_destinations():
    """
    Get list of popular destinations
    """
    destinations = [
        "Paris, France",
        "Barcelona, Spain",
        "Amsterdam, Netherlands",
        "Rome, Italy",
        "London, England",
        "Tokyo, Japan",
        "New York, USA",
        "Dubai, UAE",
        "Bangkok, Thailand",
        "Sydney, Australia"
    ]
    return {"destinations": destinations}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
