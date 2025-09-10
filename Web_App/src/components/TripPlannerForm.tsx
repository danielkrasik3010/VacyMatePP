import React, { useState } from 'react';
import { MapPin, Calendar, Plane } from 'lucide-react';

export interface TripRequest {
  current_location: string;
  destination: string;
  travel_dates: string;
}

interface TripPlannerFormProps {
  onSubmit: (request: TripRequest) => void;
  loading: boolean;
}

export const TripPlannerForm: React.FC<TripPlannerFormProps> = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    current_location: '',
    destination: '',
    startDate: '',
    endDate: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const { startDate, endDate, ...rest } = formData;
    onSubmit({
      ...rest,
      travel_dates: `${startDate} to ${endDate}`
    });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const isFormValid = () => {
    return (
      formData.current_location.length > 0 &&
      formData.destination.length > 0 &&
      formData.startDate &&
      formData.endDate
    );
  };
  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-2xl shadow-xl">
      <div className="mb-8 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Plan Your Perfect Getaway</h2>
        <p className="text-gray-600">Enter your trip details to get started</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="current_location">
            Where are you traveling from?
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MapPin className="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="current_location"
              name="current_location"
              type="text"
              className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g. New York, USA"
              value={formData.current_location}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="destination">
            Where do you want to go?
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MapPin className="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="destination"
              name="destination"
              type="text"
              className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g. Paris, France"
              value={formData.destination}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="startDate">
              Check-in
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Calendar className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="startDate"
                name="startDate"
                type="date"
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={formData.startDate}
                onChange={handleChange}
                min={new Date().toISOString().split('T')[0]}
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="endDate">
              Check-out
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Calendar className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="endDate"
                name="endDate"
                type="date"
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={formData.endDate}
                onChange={handleChange}
                min={formData.startDate || new Date().toISOString().split('T')[0]}
                disabled={!formData.startDate}
                required
              />
            </div>
          </div>
        </div>

        <div className="pt-4">
          <button
            type="submit"
            disabled={!isFormValid() || loading}
            className={`w-full px-6 py-3 rounded-lg font-medium text-white flex items-center justify-center ${
              !isFormValid() || loading
                ? 'bg-blue-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {loading ? 'Planning...' : 'Plan My Trip'}
            <Plane className="h-5 w-5 ml-2" />
          </button>
        </div>
      </form>
    </div>
  );
};