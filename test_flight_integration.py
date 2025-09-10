#!/usr/bin/env python3
"""
Test script to verify Flight_prices_tool integration with VacayMate system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

def test_flight_integration():
    """Test that the VacayMate system correctly calls the flight tool"""
    print("=== TESTING FLIGHT TOOL INTEGRATION ===")
    
    # Import the researcher node function
    from nodes.VacayMate_nodes import researcher_node
    from states.VacayMate_state import VacayMateState
    
    # Create a test state
    test_state = VacayMateState(
        user_request="Plan a vacation",
        current_location="barcelona",
        destination="amsterdam", 
        travel_dates="2025-09-15 to 2025-09-20",
        manager_brief="Test flight integration",
        research_results="",
        quotation={},
        itinerary_draft="",
        final_plan=""
    )
    
    print(f"Testing flight search from {test_state['current_location']} to {test_state['destination']}")
    print(f"Travel dates: {test_state['travel_dates']}")
    
    # Test the researcher node which should call the flight tool
    try:
        result = researcher_node(test_state)
        print("\n=== RESEARCHER NODE RESULT ===")
        
        # Check if flight data is present in results
        research_results = result.get('research_results', '')
        
        print(f"Research results length: {len(str(research_results))}")
        
        # Check for flight-related keywords
        flight_keywords = ['flight', 'airline', 'departure', 'arrival', 'price', 'USD', 'EUR']
        found_keywords = [kw for kw in flight_keywords if kw.lower() in str(research_results).lower()]
        
        print(f"Flight keywords found: {found_keywords}")
        
        # Check for specific flight data structures
        if 'itineraries' in str(research_results):
            print("✅ Flight itineraries found in results")
        else:
            print("❌ No flight itineraries found")
            
        if any(price in str(research_results) for price in ['$', 'USD', 'EUR']):
            print("✅ Flight prices found in results")
        else:
            print("❌ No flight prices found")
            
        return result
        
    except Exception as e:
        print(f"❌ Error testing flight integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_flight_integration()
