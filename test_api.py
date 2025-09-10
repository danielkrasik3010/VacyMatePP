import requests
import json

# Test the API endpoint
try:
    url = "http://localhost:8000/plan-trip"
    payload = {
        "current_location": "New York",
        "destination": "Paris",
        "travel_dates": "2025-09-15 to 2025-09-20",
        "startDate": "2025-09-15",
        "endDate": "2025-09-20",
        "travelers": 2
    }
    
    print("Sending request to:", url)
    print("Payload:", json.dumps(payload, indent=2))
    
    response = requests.post(url, json=payload)
    
    print("\nResponse Status Code:", response.status_code)
    print("Response Headers:", dict(response.headers))
    print("Response Body:", response.text)
    
except Exception as e:
    print("Error:", str(e))
