import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { TripRequest, TripPlan } from '../types';

export const useVacayMate = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPlan, setCurrentPlan] = useState<TripPlan | null>(null);

  const planTrip = useCallback(async (request: TripRequest) => {
    setLoading(true);
    setError(null);
    
    try {
      // Call the VacayMate multi-agent system through our backend
      const plan = await api.planTrip(request);
      
      setCurrentPlan(plan);
      return plan;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getDestinations = useCallback(async () => {
    try {
      return await api.getDestinations();
    } catch (err) {
      console.error('Failed to fetch destinations:', err);
      return [];
    }
  }, []);

  const checkBackendHealth = useCallback(async () => {
    return await api.healthCheck();
  }, []);

  return {
    loading,
    error,
    currentPlan,
    planTrip,
    getDestinations,
    checkBackendHealth,
    clearError: () => setError(null)
  };
};