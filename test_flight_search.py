import os
from dotenv import load_dotenv
import sys
import os

# Add the code directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.tools.Flights_prices_tool import get_flight_prices

def test_flight_search():
    print("Starting flight search test...")
    # Load environment variables
    load_dotenv()
    
    # Check if API key is loaded
    api_key = os.getenv("FLIGHTS_RAPID_API_KEY")
    if not api_key:
        print("ERROR: FLIGHTS_RAPID_API_KEY environment variable is not set!")
        print("Please set this in your .env file in the backend directory.")
        return
    else:
        print(f"API key found: {api_key[:5]}...{api_key[-5:]}")
    
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
    
    print("Testing flight search with parameters:")
    for key, value in test_params.items():
        print(f"{key}: {value}")
    
    # Make the API call
    print("\nMaking flight search request...")
    try:
        result = get_flight_prices.invoke(test_params)
        print("\nFlight search results:")
        print("-" * 50)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            if 'response_text' in result:
                print(f"Response: {result['response_text']}")
        else:
            # Print debug info if available
            if 'debug_info' in result:
                print("Debug Info:")
                for key, value in result['debug_info'].items():
                    print(f"  {key}: {value}")
                print("\n" + "-" * 50 + "\n")
            
            # Print flight itineraries
            itineraries = result.get('itineraries', [])
            if itineraries:
                print(f"Found {len(itineraries)} flight options:")
                for i, itin in enumerate(itineraries, 1):
                    print(f"\nOption {i}:")
                    print(f"Price: ${itin.get('priceUSD', 'N/A')} (€{itin.get('priceEUR', 'N/A')})")
                    print(f"Outbound: {itin.get('outbound', {}).get('summary', 'No outbound info')}")
                    print(f"Inbound: {itin.get('inbound', {}).get('summary', 'No return info')}")
                    print(f"Duration: Outbound {itin.get('durationOutbound', 'N/A')}, Inbound {itin.get('durationInbound', 'N/A')}")
                    if 'bookingUrl' in itin and itin['bookingUrl']:
                        print(f"Book at: {itin['bookingUrl']}")
            else:
                print("No flight itineraries found.")
                print("Raw response:", result)
    
    except Exception as e:
        print(f"Exception during flight search: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flight_search()
