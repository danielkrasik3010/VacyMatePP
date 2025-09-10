import React, { useState } from 'react';
import { HomePage } from './pages/HomePage';
import { ResultsPage } from './pages/ResultsPage';
import { TripPlan } from './services/api';

function App() {
  const [currentPage, setCurrentPage] = useState<'home' | 'results'>('home');
  const [tripPlan, setTripPlan] = useState<TripPlan | null>(null);

  const handleTripPlanned = (plan: TripPlan) => {
    setTripPlan(plan);
    setCurrentPage('results');
  };

  const handleBackToHome = () => {
    setCurrentPage('home');
    setTripPlan(null);
  };

  return (
    <>
      {currentPage === 'home' && (
        <HomePage onTripPlanned={handleTripPlanned} />
      )}
      {currentPage === 'results' && tripPlan && (
        <ResultsPage tripPlan={tripPlan} onBack={handleBackToHome} />
      )}
    </>
  );
}

export default App;
