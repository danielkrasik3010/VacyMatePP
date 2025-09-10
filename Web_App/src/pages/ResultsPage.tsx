import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Download, Share2, Calendar, MapPin, Plane, Hotel, Map, DollarSign, Users, Loader2 } from 'lucide-react';
import { TripPlan } from '../services/api';

interface ResultsPageProps {
  tripPlan: TripPlan;
  onBack: () => void;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      when: "beforeChildren"
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.5
    }
  }
};

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'flights', label: 'Flights' },
  { id: 'hotels', label: 'Hotels' },
  { id: 'events', label: 'Events' },
  { id: 'itinerary', label: 'Itinerary' }
];

export const ResultsPage: React.FC<ResultsPageProps> = ({ tripPlan, onBack }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: 'pdf' | 'markdown' | 'email') => {
    setIsExporting(true);
    try {
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 1500));
      console.log(`Exported as ${format}`);
      // TODO: Implement actual export functionality
      // This would typically involve:
      // 1. Formatting the trip data
      // 2. Generating a PDF/email/markdown
      // 3. Triggering download or send email
    } catch (error) {
      console.error('Export failed:', error);
      // TODO: Show error toast to user
    } finally {
      setIsExporting(false);
    }
  };

  // Helper function to render content based on active tab
  const renderTabContent = () => {
    switch (activeTab) {
      case 'flights':
        return (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold mb-4">Available Flights</h3>
            {tripPlan.flights?.length > 0 ? (
              tripPlan.flights.map((flight: any, index: number) => (
                <div key={index} className="bg-white p-4 rounded-lg shadow">
                  <div className="flex items-center">
                    <Plane className="text-blue-500 mr-3" />
                    <div>
                      <p className="font-medium">{flight.airline} - {flight.flight_number}</p>
                      <p className="text-sm text-gray-600">
                        {flight.departure_airport} → {flight.arrival_airport}
                      </p>
                      <p className="text-sm text-gray-500">
                        {flight.departure_time} - {flight.arrival_time} • {flight.duration}
                      </p>
                      <p className="text-sm font-medium text-green-600 mt-1">
                        ${flight.price} {flight.currency}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500">No flight information available.</p>
            )}
          </div>
        );
      case 'hotels':
        return (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold mb-4">Recommended Hotels</h3>
            {tripPlan.hotels?.length > 0 ? (
              tripPlan.hotels.map((hotel: any, index: number) => (
                <div key={index} className="bg-white p-4 rounded-lg shadow">
                  <div className="flex items-start">
                    <Hotel className="text-indigo-500 mr-3 mt-1 flex-shrink-0" />
                    <div className="flex-grow">
                      <div className="flex justify-between">
                        <h4 className="font-medium">{hotel.name}</h4>
                        <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          {hotel.rating}★
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{hotel.address}</p>
                      <p className="text-sm text-gray-700 mt-2">{hotel.description}</p>
                      <div className="mt-2">
                        <span className="text-lg font-semibold text-gray-900">
                          ${hotel.price_per_night}
                        </span>
                        <span className="text-sm text-gray-500"> / night</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500">No hotel information available.</p>
            )}
          </div>
        );
      case 'events':
        return (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold mb-4">Upcoming Events</h3>
            {tripPlan.events?.length > 0 ? (
              tripPlan.events.map((event: any, index: number) => (
                <div key={index} className="bg-white p-4 rounded-lg shadow">
                  <h4 className="font-medium">{event.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    <Calendar className="inline mr-1 w-4 h-4" />
                    {event.date}
                  </p>
                  {event.location && (
                    <p className="text-sm text-gray-600 mt-1">
                      <MapPin className="inline mr-1 w-4 h-4" />
                      {event.location}
                    </p>
                  )}
                  {event.price && (
                    <p className="text-sm text-gray-600 mt-1">
                      <DollarSign className="inline mr-1 w-4 h-4" />
                      {event.price}
                    </p>
                  )}
                  {event.description && (
                    <p className="text-sm text-gray-700 mt-2">{event.description}</p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-gray-500">No events found for your travel dates.</p>
            )}
          </div>
        );
      case 'itinerary':
        return (
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">Your Itinerary</h3>
            {tripPlan.itinerary ? (
              <div className="prose max-w-none" 
                   dangerouslySetInnerHTML={{ __html: tripPlan.itinerary.replace(/\n/g, '<br />') }} />
            ) : (
              <p className="text-gray-500">No detailed itinerary available.</p>
            )}
          </div>
        );
      default: // overview
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-xl font-semibold mb-4">Trip Summary</h3>
              {tripPlan.itinerary && (
                <div className="prose max-w-none mb-6" 
                     dangerouslySetInnerHTML={{ __html: tripPlan.itinerary.split('\n').slice(0, 3).join('<br />') + '...' }} />
              )}
              <button 
                onClick={() => setActiveTab('itinerary')}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                View Full Itinerary →
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <h4 className="font-medium mb-3 flex items-center">
                  <Plane className="text-blue-500 mr-2" />
                  Flights
                </h4>
                {tripPlan.flights?.length > 0 ? (
                  <div className="space-y-3">
                    {tripPlan.flights.slice(0, 2).map((flight: any, index: number) => (
                      <div key={index} className="text-sm">
                        <p className="font-medium">{flight.airline}</p>
                        <p className="text-gray-600">
                          {flight.departure_airport} → {flight.arrival_airport}
                        </p>
                        <p className="text-gray-500 text-xs">
                          {flight.departure_time} • {flight.duration}
                        </p>
                      </div>
                    ))}
                    {tripPlan.flights.length > 2 && (
                      <button 
                        onClick={() => setActiveTab('flights')}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        View all {tripPlan.flights.length} flights →
                      </button>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No flight information available.</p>
                )}
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <h4 className="font-medium mb-3 flex items-center">
                  <Hotel className="text-indigo-500 mr-2" />
                  Hotels
                </h4>
                {tripPlan.hotels?.length > 0 ? (
                  <div className="space-y-3">
                    {tripPlan.hotels.slice(0, 1).map((hotel: any, index: number) => (
                      <div key={index} className="text-sm">
                        <p className="font-medium">{hotel.name}</p>
                        <p className="text-gray-600">{hotel.address}</p>
                        <p className="text-gray-500">
                          ${hotel.price_per_night} <span className="text-xs">/ night</span>
                        </p>
                        <div className="mt-1">
                          <span className="text-yellow-500">
                            {'★'.repeat(Math.round(hotel.rating))}
                            {'☆'.repeat(5 - Math.round(hotel.rating))}
                          </span>
                        </div>
                      </div>
                    ))}
                    {tripPlan.hotels.length > 1 && (
                      <button 
                        onClick={() => setActiveTab('hotels')}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        View all {tripPlan.hotels.length} hotels →
                      </button>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No hotel information available.</p>
                )}
              </div>
            </div>

            {tripPlan.events?.length > 0 && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h4 className="font-medium mb-3 flex items-center">
                  <Map className="text-green-500 mr-2" />
                  Upcoming Events
                </h4>
                <div className="space-y-3">
                  {tripPlan.events.slice(0, 3).map((event: any, index: number) => (
                    <div key={index} className="text-sm border-l-2 border-green-200 pl-3">
                      <p className="font-medium">{event.title}</p>
                      <p className="text-gray-600 text-xs">
                        {event.date} • {event.location}
                      </p>
                    </div>
                  ))}
                  {tripPlan.events.length > 3 && (
                    <button 
                      onClick={() => setActiveTab('events')}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      View all {tripPlan.events.length} events →
                    </button>
                  )}
                </div>
              </div>
            )}

            {tripPlan.total_cost && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h4 className="font-medium mb-3 flex items-center">
                  <DollarSign className="text-yellow-500 mr-2" />
                  Estimated Cost
                </h4>
                <div className="text-2xl font-bold text-gray-800">
                  {tripPlan.total_cost}
                </div>
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50"
    >
      {/* Header */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-40 shadow-sm"
      >
        <div className="max-w-7xl mx-auto px-4 py-4">
          <motion.div className="flex items-center justify-between" variants={itemVariants}>
            <div className="flex items-center">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onBack}
                className="p-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Go back"
              >
                <ArrowLeft className="w-5 h-5" />
              </motion.button>
              <h1 className="ml-4 text-xl font-semibold text-gray-800 truncate max-w-xs md:max-w-md">
                {tripPlan.itinerary?.split('\n')[0] || 'Your Trip Plan'}
              </h1>
            </div>
            <motion.div className="flex items-center space-x-3" variants={itemVariants}>
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => handleExport('pdf')}
                disabled={isExporting}
                className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                  isExporting 
                    ? 'bg-indigo-400 cursor-not-allowed' 
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                }`}
              >
                {isExporting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    Export PDF
                  </>
                )}
              </motion.button>
              <motion.button 
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </motion.button>
            </motion.div>
          </motion.div>
        </div>
      </motion.div>

      {/* Main Content */}
      <AnimatePresence mode="wait">
        <motion.div 
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="max-w-7xl mx-auto px-4 py-8"
        >
          {/* Tab Navigation */}
          <motion.div 
            variants={containerVariants}
            className="mb-8 border-b border-gray-200"
          >
            <nav className="-mb-px flex space-x-8 overflow-x-auto" aria-label="Tabs">
              {tabs.map((tab) => (
                <motion.button
                  key={tab.id}
                  variants={itemVariants}
                  onClick={() => setActiveTab(tab.id)}
                  className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {tab.label}
                  {activeTab === tab.id && (
                    <motion.div 
                      layoutId="activeTab"
                      className="h-0.5 bg-indigo-500 mt-1"
                      transition={{
                        type: "spring",
                        stiffness: 300,
                        damping: 30
                      }}
                    />
                  )}
                </motion.button>
              ))}
            </nav>
          </motion.div>
          
          {/* Tab Content */}
          <motion.div 
            variants={containerVariants}
            className="bg-white/70 backdrop-blur-sm rounded-xl p-6 shadow-sm border border-gray-100"
          >
            {renderTabContent()}
          </motion.div>
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
};