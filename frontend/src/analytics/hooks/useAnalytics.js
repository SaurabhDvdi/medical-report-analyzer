import { useQuery } from '@tanstack/react-query'
import { getHealthSummaryJson, getCorrelationJson, getParameterTrend } from '../../services/analyticsService'

// Hook for health summary JSON data
export const useHealthSummaryJson = () => {
  return useQuery({
    queryKey: ['healthSummaryJson'],
    queryFn: getHealthSummaryJson,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Hook for parameter correlation JSON data
export const useCorrelationJson = () => {
  return useQuery({
    queryKey: ['correlationJson'],
    queryFn: getCorrelationJson,
    staleTime: 1000 * 60 * 5,
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