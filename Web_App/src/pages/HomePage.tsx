import { useState } from 'react';
import { TripPlannerForm } from '../components/TripPlannerForm';
import { TripPlan } from '../services/api';

interface HomePageProps {
  onTripPlanned: (plan: TripPlan) => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onTripPlanned }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (tripData: any) => {
    setLoading(true);
    setError(null);
    try {
      // Format the request data to match backend expectations
      const requestData = {
        current_location: tripData.current_location,
        destination: tripData.destination,
        travel_dates: `${tripData.startDate} to ${tripData.endDate}`,
        startDate: tripData.startDate,
        endDate: tripData.endDate
      };

      console.log('Sending request to backend:', requestData);
      
      const response = await fetch('http://localhost:8000/plan-trip', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
          console.error('Backend error details:', errorData);
        } catch (e) {
          console.error('Failed to parse error response');
        }
        throw new Error(`HTTP error! status: ${response.status}${errorData ? ` - ${JSON.stringify(errorData)}` : ''}`);
      }

      const result = await response.json();
      onTripPlanned(result);
    } catch (error) {
      console.error('Error planning trip:', error);
      setError('Failed to plan trip. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-indigo-600 to-blue-500">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 py-24 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Plan Your Perfect Getaway
            </h1>
            <p className="mt-6 max-w-2xl mx-auto text-xl text-indigo-100">
              AI-powered vacation planning that saves you time and money.
            </p>
          </div>

          {/* Trip Planner Form */}
          <div className="mt-12 max-w-3xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
              <div className="p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Where to next?</h2>
                {error && (
                  <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-md">
                    {error}
                  </div>
                )}
                <TripPlannerForm onSubmit={handleSubmit} loading={loading} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};