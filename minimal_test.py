import sys
import os

# Add the code directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

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
try:
    result = get_flight_prices.invoke(test_params)
    print("Result:")
    print(result)
except Exception as e:
    print(f"Error: {str(e)}")
