import sys
sys.path.append('code/tools')
from Make_quotation_tool import calculate_vacation_cost

# Test with realistic data
hotel_prices = [120, 150, 130, 140]  # per night
flight_prices = [450, 500, 475]     # round-trip
start_date = '2025-09-10'
end_date = '2025-09-17'  # 7 days
destination = 'Dubrovnik'

print("=== TESTING QUOTATION TOOL ===")
print(f"Hotel prices: {hotel_prices}")
print(f"Flight prices: {flight_prices}")
print(f"Dates: {start_date} to {end_date}")
print(f"Destination: {destination}")
print()

try:
    result = calculate_vacation_cost(hotel_prices, flight_prices, start_date, end_date, destination)
    
    print("=== QUOTATION RESULTS ===")
    print(f"Days: {result['days']}")
    print(f"Hotel total: ${result['hotel_total']}")
    print(f"Flight total: ${result['flight_total']}")
    print(f"Daily cost estimate: ${result['daily_cost_estimate']}")
    print(f"Daily total: ${result['daily_total']}")
    print(f"Subtotal: ${result['subtotal']}")
    print(f"Commission (10%): ${result['commission_amount']}")
    print(f"Final quotation: ${result['final_quotation']}")
    print()
    
    print("=== MANUAL VERIFICATION ===")
    avg_hotel = sum(hotel_prices) / len(hotel_prices)
    avg_flight = sum(flight_prices) / len(flight_prices)
    days = 7
    
    print(f"Avg hotel per night: ${avg_hotel}")
    print(f"Hotel total ({avg_hotel} x {days} days): ${avg_hotel * days}")
    print(f"Avg flight: ${avg_flight}")
    print(f"Expected subtotal (before daily costs): ${avg_hotel * days + avg_flight}")
    
    # Verify calculations
    expected_hotel_total = avg_hotel * days
    expected_flight_total = avg_flight
    
    print()
    print("=== VERIFICATION ===")
    print(f"Hotel calculation correct: {abs(result['hotel_total'] - expected_hotel_total) < 0.01}")
    print(f"Flight calculation correct: {abs(result['flight_total'] - expected_flight_total) < 0.01}")
    
except Exception as e:
    print(f"Error testing quotation tool: {e}")
