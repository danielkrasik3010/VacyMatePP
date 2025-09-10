import React from 'react';
import { motion } from 'framer-motion';
import { Plane, Clock, DollarSign } from 'lucide-react';
import { FlightOption } from '../types';

interface FlightCardProps {
  flight: FlightOption;
  index: number;
}

export const FlightCard: React.FC<FlightCardProps> = ({ flight, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mr-4">
            <Plane className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">{flight.airline}</h3>
            <p className="text-sm text-gray-600">
              {flight.stops === 0 ? 'Direct' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-indigo-600">${flight.price}</div>
          <div className="text-sm text-gray-600">per person</div>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-gray-600 mb-4">
        <div className="flex items-center">
          <Clock className="w-4 h-4 mr-1" />
          <span>{flight.duration}</span>
        </div>
        <div className="flex items-center space-x-4">
          <span className="font-medium">{flight.departure}</span>
          <span>→</span>
          <span className="font-medium">{flight.arrival}</span>
        </div>
      </div>

      <button className="w-full bg-indigo-600 text-white py-3 rounded-xl font-medium hover:bg-indigo-700 transition-colors">
        Select Flight
      </button>
    </motion.div>
  );
};