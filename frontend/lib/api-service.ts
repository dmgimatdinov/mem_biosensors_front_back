/**
 * API Service Layer
 * Provides typed HTTP request functions for all backend endpoints
 */

import { API_BASE_URL, API_ENDPOINTS, API_CONFIG } from "./api-config"
import type {
  Analyte,
  BioRecognitionLayer,
  ImmobilizationLayer,
  MemristiveLayer,
  SensorCombination,
} from "./biosensor-store"

/**
 * API Response Types
 */
interface SuccessResponse {
  success: boolean
  message: string
  data?: any
}

interface ErrorResponse {
  detail: string
}

interface SynthesizeResponse {
  success: boolean
  checked: number
  created: number
  message: string
}

interface StatisticsResponse {
  total_analytes: number
  total_bio_recognition: number
  total_immobilization: number
  total_memristive: number
  total_combinations: number
  average_score: number
}

/**
 * API Error Class
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: any
  ) {
    super(message)
    this.name = "ApiError"
  }
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...API_CONFIG.headers,
        ...options.headers,
      },
    })

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`
      try {
        const errorData: ErrorResponse = await response.json()
        errorMessage = errorData.detail || errorMessage
      } catch {
        // If parsing fails, use status text
      }
      throw new ApiError(errorMessage, response.status)
    }

    return await response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error instanceof Error) {
      throw new ApiError(`Network error: ${error.message}`)
    }
    throw new ApiError("Unknown error occurred")
  }
}

/**
 * Health Check
 */
export async function checkHealth(): Promise<{ status: string; message: string }> {
  return fetchApi(API_ENDPOINTS.health)
}

/**
 * Analytes API
 */
export async function getAnalytes(limit = 50, offset = 0): Promise<Analyte[]> {
  return fetchApi(`${API_ENDPOINTS.analytes}?limit=${limit}&offset=${offset}`)
}

export async function createAnalyte(analyte: Analyte): Promise<SuccessResponse> {
  return fetchApi(API_ENDPOINTS.analytes, {
    method: "POST",
    body: JSON.stringify(analyte),
  })
}

/**
 * Bio Recognition Layers API
 */
export async function getBioRecognitionLayers(limit = 50, offset = 0): Promise<BioRecognitionLayer[]> {
  return fetchApi(`${API_ENDPOINTS.bioRecognition}?limit=${limit}&offset=${offset}`)
}

export async function createBioRecognitionLayer(layer: BioRecognitionLayer): Promise<SuccessResponse> {
  return fetchApi(API_ENDPOINTS.bioRecognition, {
    method: "POST",
    body: JSON.stringify(layer),
  })
}

/**
 * Immobilization Layers API
 */
export async function getImmobilizationLayers(limit = 50, offset = 0): Promise<ImmobilizationLayer[]> {
  return fetchApi(`${API_ENDPOINTS.immobilization}?limit=${limit}&offset=${offset}`)
}

export async function createImmobilizationLayer(layer: ImmobilizationLayer): Promise<SuccessResponse> {
  return fetchApi(API_ENDPOINTS.immobilization, {
    method: "POST",
    body: JSON.stringify(layer),
  })
}

/**
 * Memristive Layers API
 */
export async function getMemristiveLayers(limit = 50, offset = 0): Promise<MemristiveLayer[]> {
  return fetchApi(`${API_ENDPOINTS.memristive}?limit=${limit}&offset=${offset}`)
}

export async function createMemristiveLayer(layer: MemristiveLayer): Promise<SuccessResponse> {
  return fetchApi(API_ENDPOINTS.memristive, {
    method: "POST",
    body: JSON.stringify(layer),
  })
}

/**
 * Combinations API
 */
export async function getCombinations(limit = 50, offset = 0): Promise<SensorCombination[]> {
  return fetchApi(`${API_ENDPOINTS.combinations}?limit=${limit}&offset=${offset}`)
}

export async function synthesizeCombinations(maxCombinations = 10000): Promise<SynthesizeResponse> {
  return fetchApi(`${API_ENDPOINTS.combinationsSynthesize}?max_combinations=${maxCombinations}`, {
    method: "POST",
  })
}

/**
 * Analytics API
 */
export async function getStatistics(): Promise<StatisticsResponse> {
  return fetchApi(API_ENDPOINTS.analyticsStatistics)
}

export async function getBestCombinations(limit = 10): Promise<SensorCombination[]> {
  return fetchApi(`${API_ENDPOINTS.analyticsBestCombinations}?limit=${limit}`)
}

export async function getComparativeAnalysis(): Promise<any> {
  return fetchApi(API_ENDPOINTS.analyticsComparative)
}

/**
 * Export API
 */
export async function exportTable(tableName: string, format: "csv" | "excel" | "pdf" = "csv"): Promise<Blob> {
  const url = `${API_BASE_URL}${API_ENDPOINTS.exportTable(tableName, format)}`
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new ApiError(`Export failed: ${response.statusText}`, response.status)
  }
  
  return response.blob()
}

export async function exportAll(format: "csv" | "excel" | "pdf" = "csv"): Promise<Blob> {
  const url = `${API_BASE_URL}${API_ENDPOINTS.exportAll(format)}`
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new ApiError(`Export failed: ${response.statusText}`, response.status)
  }
  
  return response.blob()
}
