import React from 'react';
import { motion } from 'framer-motion';
import { Cloud, Sun, CloudRain, Wind, Droplets } from 'lucide-react';
import { WeatherData } from '../types';

interface WeatherCardProps {
  weather: WeatherData;
  index: number;
}

const getWeatherIcon = (condition: string) => {
  switch (condition) {
    case 'sunny':
      return <Sun className="w-8 h-8 text-yellow-500" />;
    case 'partly-cloudy':
      return <Cloud className="w-8 h-8 text-gray-400" />;
    case 'cloudy':
      return <Cloud className="w-8 h-8 text-gray-600" />;
    case 'rainy':
      return <CloudRain className="w-8 h-8 text-blue-500" />;
    default:
      return <Sun className="w-8 h-8 text-yellow-500" />;
  }
};

export const WeatherCard: React.FC<WeatherCardProps> = ({ weather, index }) => {
  const date = new Date(weather.date);
  const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
  const dayNumber = date.getDate();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 min-w-[200px] border border-white/20"
    >
      <div className="text-center mb-4">
        <div className="text-sm font-medium text-gray-600 mb-1">{dayName}</div>
        <div className="text-2xl font-bold text-gray-800">{dayNumber}</div>
      </div>

      <div className="flex justify-center mb-4">
        {getWeatherIcon(weather.condition)}
      </div>

      <div className="text-center mb-4">
        <div className="text-3xl font-bold text-gray-800 mb-1">
          {weather.temperature}°
        </div>
        <div className="text-sm text-gray-600 capitalize">
          {weather.condition.replace('-', ' ')}
        </div>
      </div>

      <div className="space-y-2 text-xs text-gray-600">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Droplets className="w-3 h-3 mr-1" />
            <span>Humidity</span>
          </div>
          <span>{weather.humidity}%</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Wind className="w-3 h-3 mr-1" />
            <span>Wind</span>
          </div>
          <span>{weather.windSpeed} mph</span>
        </div>
      </div>
    </motion.div>
  );
};