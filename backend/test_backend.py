"""
Simple test script to verify the VacayMate backend API
"""

import requests
import json
import sys

def test_backend_health():
    """Test if the backend server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def test_destinations_endpoint():
    """Test the destinations endpoint"""
    try:
        response = requests.get("http://localhost:8000/destinations", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Destinations endpoint working")
            print(f"Available destinations: {len(data['destinations'])}")
            return True
        else:
            print(f"❌ Destinations endpoint returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing destinations endpoint: {e}")
        return False

def test_plan_trip_endpoint():
    """Test the plan-trip endpoint with sample data"""
    try:
        test_request = {
            "destination": "Paris",
            "startDate": "2025-09-15",
            "endDate": "2025-09-20",
            "travelers": 2,
            "budget": 2000.0,
            "preferences": {}
        }
        
        print("🚀 Testing plan-trip endpoint...")
        print(f"Request: {json.dumps(test_request, indent=2)}")
        
        response = requests.post(
            "http://localhost:8000/plan-trip", 
            json=test_request,
            timeout=60  # Give it time to process
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Plan-trip endpoint working")
            print(f"Response keys: {list(data.keys())}")
            print(f"Destination: {data.get('destination')}")
            print(f"Flights found: {len(data.get('flights', []))}")
            print(f"Hotels found: {len(data.get('hotels', []))}")
            print(f"Activities found: {len(data.get('activities', []))}")
            return True
        else:
            print(f"❌ Plan-trip endpoint returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing plan-trip endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing VacayMate Backend API")
    print("=" * 50)
    
    # Test health endpoint
    if not test_backend_health():
        print("\n❌ Backend server is not running. Please start it first:")
        print("cd backend")
        print("python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    print("\n" + "-" * 50)
    
    # Test destinations endpoint
    test_destinations_endpoint()
    
    print("\n" + "-" * 50)
    
    # Test plan-trip endpoint (this will take longer)
    print("⚠️  This test will take 30-60 seconds as it calls the VacayMate system...")
    test_plan_trip_endpoint()
    
    print("\n" + "=" * 50)
    print("🏁 Backend API testing completed")
