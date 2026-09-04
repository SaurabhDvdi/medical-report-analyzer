import { useQuery } from '@tanstack/react-query'
import { getHealthSummaryJson, getParameterTrend } from '../../services/analyticsService'

// Hook for health summary JSON data
export const useHealthSummaryJson = () => {
  return useQuery({
    queryKey: ['healthSummaryJson'],
    queryFn: getHealthSummaryJson,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Hook for lab parameter trend data
export const useParameterTrend = (parameterName) => {
  return useQuery({
    queryKey: ['parameterTrend', parameterName],
    queryFn: () => getParameterTrend(parameterName),
    enabled: Boolean(parameterName),
    staleTime: 1000 * 60 * 5,
  })
}