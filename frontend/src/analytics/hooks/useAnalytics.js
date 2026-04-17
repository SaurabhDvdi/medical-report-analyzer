import { useQuery } from '@tanstack/react-query'
import { getStructuredHealthData } from '../services/analyticsService'

// Hook for structured health data (prepared for future interactive charts)
export const useStructuredHealthData = () => {
  return useQuery({
    queryKey: ['structured-health-data'],
    queryFn: getStructuredHealthData,
    enabled: false, // Disabled by default until charts are implemented
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Hook for health summary blob data (current implementation)
export const useHealthSummary = () => {
  return useQuery({
    queryKey: ['health-summary'],
    queryFn: () => getStructuredHealthData(), // Will be replaced with structured data later
    staleTime: 1000 * 60 * 5,
  })
}