import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Import the flight search function
from tools.Flights_prices_tool import get_flight_prices

# Test parameters
test_params = {
    'source': 'paris',
    'destination': 'milan',
    'adults': 1,
    'currency': 'USD',
    'outboundDepartureDateStart': '2025-09-15T00:00:00',
    'outboundDepartureDateEnd': '2025-09-15T23:59:59',
    'inboundDepartureDateStart': '2025-09-20T00:00:00',
    'inboundDepartureDateEnd': '2025-09-20T23:59:59'
}

print("Testing flight search...")
print(f"API Key: {'Set' if os.getenv('FLIGHTS_RAPID_API_KEY') else 'Not set'}")

try:
    print("\nCalling get_flight_prices...")
    result = get_flight_prices.invoke(test_params)
    print("\nResult:")
    print(result)
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
