/**
 * Custom React Hooks for Biosensor Data Management
 * Provides hooks for fetching and managing data from the backend API
 */

import { useState, useEffect, useCallback } from "react"
import {
  getAnalytes,
  getBioRecognitionLayers,
  getImmobilizationLayers,
  getMemristiveLayers,
  getCombinations,
  createAnalyte,
  createBioRecognitionLayer,
  createImmobilizationLayer,
  createMemristiveLayer,
  synthesizeCombinations,
  getStatistics,
  getBestCombinations,
  ApiError,
} from "@/lib/api-service"
import type {
  Analyte,
  BioRecognitionLayer,
  ImmobilizationLayer,
  MemristiveLayer,
  SensorCombination,
  StoreData,
} from "@/lib/biosensor-store"

/**
 * Hook State Interface
 */
interface UseDataState<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

/**
 * Generic data fetching hook
 */
function useDataFetch<T>(
  fetchFn: () => Promise<T>,
  dependencies: any[] = []
): UseDataState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchFn()
      setData(result)
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : "Failed to fetch data"
      setError(errorMessage)
      console.error("Data fetch error:", err)
    } finally {
      setLoading(false)
    }
  }, [fetchFn])

  useEffect(() => {
    refetch()
  }, dependencies)

  return { data, loading, error, refetch }
}

/**
 * Hook to fetch all biosensor data (replaces localStorage)
 */
export function useBiosensorData(): UseDataState<StoreData> & {
  createNewAnalyte: (analyte: Analyte) => Promise<void>
  createNewBioRecognition: (layer: BioRecognitionLayer) => Promise<void>
  createNewImmobilization: (layer: ImmobilizationLayer) => Promise<void>
  createNewMemristive: (layer: MemristiveLayer) => Promise<void>
  synthesizeNewCombinations: (max: number) => Promise<{ checked: number; created: number }>
} {
  const [data, setData] = useState<StoreData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAllData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      // Fetch all data in parallel
      const [analytes, bioRecognitions, immobilizations, memristives, combinations] = await Promise.all([
        getAnalytes(1000, 0),
        getBioRecognitionLayers(1000, 0),
        getImmobilizationLayers(1000, 0),
        getMemristiveLayers(1000, 0),
        getCombinations(1000, 0),
      ])

      setData({
        analytes,
        bioRecognitions,
        immobilizations,
        memristives,
        combinations,
        passports: [], // Passports are not used in current implementation
      })
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : "Failed to fetch biosensor data"
      setError(errorMessage)
      console.error("Biosensor data fetch error:", err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAllData()
  }, [fetchAllData])

  const createNewAnalyte = useCallback(
    async (analyte: Analyte) => {
      await createAnalyte(analyte)
      await fetchAllData()
    },
    [fetchAllData]
  )

  const createNewBioRecognition = useCallback(
    async (layer: BioRecognitionLayer) => {
      await createBioRecognitionLayer(layer)
      await fetchAllData()
    },
    [fetchAllData]
  )

  const createNewImmobilization = useCallback(
    async (layer: ImmobilizationLayer) => {
      await createImmobilizationLayer(layer)
      await fetchAllData()
    },
    [fetchAllData]
  )

  const createNewMemristive = useCallback(
    async (layer: MemristiveLayer) => {
      await createMemristiveLayer(layer)
      await fetchAllData()
    },
    [fetchAllData]
  )

  const synthesizeNewCombinations = useCallback(
    async (max: number) => {
      const result = await synthesizeCombinations(max)
      await fetchAllData()
      return { checked: result.checked, created: result.created }
    },
    [fetchAllData]
  )

  return {
    data,
    loading,
    error,
    refetch: fetchAllData,
    createNewAnalyte,
    createNewBioRecognition,
    createNewImmobilization,
    createNewMemristive,
    synthesizeNewCombinations,
  }
}

/**
 * Hook to fetch statistics
 */
export function useStatistics() {
  return useDataFetch(getStatistics, [])
}

/**
 * Hook to fetch best combinations
 */
export function useBestCombinations(limit = 10) {
  return useDataFetch(() => getBestCombinations(limit), [limit])
}

/**
 * Hook to fetch analytes only
 */
export function useAnalytes(limit = 50, offset = 0) {
  return useDataFetch(() => getAnalytes(limit, offset), [limit, offset])
}

/**
 * Hook to fetch bio recognition layers only
 */
export function useBioRecognitionLayers(limit = 50, offset = 0) {
  return useDataFetch(() => getBioRecognitionLayers(limit, offset), [limit, offset])
}

/**
 * Hook to fetch immobilization layers only
 */
export function useImmobilizationLayers(limit = 50, offset = 0) {
  return useDataFetch(() => getImmobilizationLayers(limit, offset), [limit, offset])
}

/**
 * Hook to fetch memristive layers only
 */
export function useMemristiveLayers(limit = 50, offset = 0) {
  return useDataFetch(() => getMemristiveLayers(limit, offset), [limit, offset])
}

/**
 * Hook to fetch combinations only
 */
export function useCombinations(limit = 50, offset = 0) {
  return useDataFetch(() => getCombinations(limit, offset), [limit, offset])
}
