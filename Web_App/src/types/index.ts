export interface TripRequest {
  destination: string;
  startDate: string;
  endDate: string;
  travelers: number;
  budget: number;
  preferences: string[];
}

export interface WeatherData {
  date: string;
  temperature: number;
  condition: string;
  icon: string;
  humidity: number;
  windSpeed: number;
}

export interface FlightOption {
  id: string;
  airline: string;
  departure: string;
  arrival: string;
  duration: string;
  price: number;
  stops: number;
}

export interface HotelOption {
  id: string;
  name: string;
  rating: number;
  price: number;
  image: string;
  amenities: string[];
  location: string;
}

export interface Activity {
  id: string;
  name: string;
  description: string;
  price: number;
  duration: string;
  rating: number;
  image: string;
  category: string;
}

export interface TripPlan {
  id: string;
  destination: string;
  dates: {
    start: string;
    end: string;
  };
  flights: FlightOption[];
  hotels: HotelOption[];
  activities: Activity[];
  weather: WeatherData[];
  totalCost: number;
  itinerary: DayPlan[];
}

export interface DayPlan {
  date: string;
  weather: WeatherData;
  activities: Activity[];
  meals: string[];
  notes: string;
}

export interface Review {
  id: string;
  name: string;
  rating: number;
  comment: string;
  avatar: string;
  country: string;
  flag: string;
}

export interface Metrics {
  vacationsPlanned: number;
  moneySaved: number;
  timeSaved: number;
}