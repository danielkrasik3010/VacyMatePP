import React from 'react';
import { motion } from 'framer-motion';
import { Star, MapPin, Wifi, Car } from 'lucide-react';
import { HotelOption } from '../types';

interface HotelCardProps {
  hotel: HotelOption;
  index: number;
}

export const HotelCard: React.FC<HotelCardProps> = ({ hotel, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      className="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300"
    >
      <div className="relative h-48">
        <img
          src={hotel.image}
          alt={hotel.name}
          className="w-full h-full object-cover"
        />
        <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg px-3 py-1">
          <div className="flex items-center">
            <Star className="w-4 h-4 text-yellow-400 fill-current mr-1" />
            <span className="font-medium text-gray-800">{hotel.rating}</span>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="text-xl font-bold text-gray-800 mb-1">{hotel.name}</h3>
            <div className="flex items-center text-gray-600">
              <MapPin className="w-4 h-4 mr-1" />
              <span className="text-sm">{hotel.location}</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-indigo-600">${hotel.price}</div>
            <div className="text-sm text-gray-600">per night</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          {hotel.amenities.slice(0, 4).map((amenity, i) => (
            <span
              key={i}
              className="px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
            >
              {amenity}
            </span>
          ))}
        </div>

        <button className="w-full bg-indigo-600 text-white py-3 rounded-xl font-medium hover:bg-indigo-700 transition-colors">
          Book Now
        </button>
      </div>
    </motion.div>
  );
};