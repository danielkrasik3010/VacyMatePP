import sys
import os
from dotenv import load_dotenv

# Add the code directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from the backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

# Import the flight search function
from code.tools.Flights_prices_tool import get_flight_prices

def main():
    print("Testing flight search...")
    
    # Check if API key is loaded
    api_key = os.getenv("FLIGHTS_RAPID_API_KEY")
    if not api_key:
        print("ERROR: FLIGHTS_RAPID_API_KEY environment variable is not set!")
        print("Please make sure to set this in your .env file in the backend directory.")
        return
    
    print("API key found.")
    
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
    
    print("\nSearching for flights with parameters:")
    for key, value in test_params.items():
        print(f"  {key}: {value}")
    
    # Make the API call
    print("\nMaking flight search request...")
    try:
        result = get_flight_prices.invoke(test_params)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            if 'response_text' in result:
                print(f"Response: {result['response_text']}")
        else:
            # Print debug info if available
            if 'debug_info' in result:
                print("\nDebug Info:")
                for key, value in result['debug_info'].items():
                    print(f"  {key}: {value}")
            
            # Print flight itineraries
            itineraries = result.get('itineraries', [])
            print(f"\nFound {len(itineraries)} flight options:")
            
            for i, itin in enumerate(itineraries[:3], 1):  # Show first 3 options
                print(f"\nOption {i}:")
                print(f"Price: ${itin.get('priceUSD', 'N/A')} (€{itin.get('priceEUR', 'N/A')})")
                
                outbound = itin.get('outbound', {})
                if outbound:
                    print(f"Outbound: {outbound.get('summary', 'No details')}")
                
                inbound = itin.get('inbound', {})
                if inbound:
                    print(f"Inbound: {inbound.get('summary', 'No details')}")
                
                if 'bookingUrl' in itin and itin['bookingUrl']:
                    print(f"Book at: {itin['bookingUrl']}")
    
    except Exception as e:
        print(f"Exception during flight search: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
