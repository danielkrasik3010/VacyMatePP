// Define types for the API service
export interface TripRequest {
  current_location: string;
  destination: string;
  travel_dates: string;
}

export interface TripPlan {
  itinerary: string;
  flights: any[];
  hotels: any[];
  events: any[];
  total_cost: string;
}

// VacayMate API service - connects to FastAPI backend
class VacayMateAPI {
  private baseUrl = 'http://localhost:8000';

  // Trip planning endpoint - connects to VacayMate multi-agent system
  async planTrip(request: TripRequest): Promise<TripPlan> {
    try {
      const response = await fetch(`${this.baseUrl}/plan-trip`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const tripPlan = await response.json();
      return tripPlan;
    } catch (error) {
      console.error('Error planning trip:', error);
      throw new Error('Failed to plan trip. Please try again.');
    }
  }

  // Get popular destinations (placeholder for future implementation)
  async getDestinations(): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/destinations`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.destinations;
    } catch (error) {
      console.error('Error fetching destinations:', error);
      return this.mockDestinations();
    }
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  }

  private mockDestinations(): string[] {
    return [
      "Paris, France",
      "Barcelona, Spain", 
      "Amsterdam, Netherlands",
      "Rome, Italy",
      "London, England",
      "Tokyo, Japan",
      "New York, USA",
      "Dubai, UAE"
    ];
  }

}

export const api = new VacayMateAPI();