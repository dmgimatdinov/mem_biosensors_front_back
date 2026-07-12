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
 * Field name mappings between frontend (snake_case) and backend (PascalCase_with_underscores)
 */
const ANALYTE_FIELD_MAP: Record<keyof Analyte, string> = {
  ta_id: "TA_ID",
  ta_name: "TA_Name",
  ph_min: "PH_Min",
  ph_max: "PH_Max",
  t_max: "T_Max",
  stability: "ST",
  half_life: "HL",
  power_consumption: "PC",
}

const BIO_RECOGNITION_FIELD_MAP: Record<keyof BioRecognitionLayer, string> = {
  bre_id: "BRE_ID",
  bre_name: "BRE_Name",
  ph_min: "PH_Min",
  ph_max: "PH_Max",
  t_min: "T_Min",
  t_max: "T_Max",
  dr_min: "DR_Min",
  dr_max: "DR_Max",
  sensitivity: "SN",
  reproducibility: "RP",
  response_time: "TR",
  stability: "ST",
  lod: "LOD",
  durability: "HL",
  power_consumption: "PC",
}

const IMMOBILIZATION_FIELD_MAP: Record<keyof ImmobilizationLayer, string> = {
  im_id: "IM_ID",
  im_name: "IM_Name",
  ph_min: "PH_Min",
  ph_max: "PH_Max",
  t_min: "T_Min",
  t_max: "T_Max",
  young_modulus: "MP",
  adhesion: "Adh",
  solubility: "Sol",
  loss_coefficient: "K_IM",
  reproducibility: "RP",
  response_time: "TR",
  stability: "ST",
  durability: "HL",
  power_consumption: "PC",
}

const MEMRISTIVE_FIELD_MAP: Record<keyof MemristiveLayer, string> = {
  mem_id: "MEM_ID",
  mem_name: "MEM_Name",
  ph_min: "PH_Min",
  ph_max: "PH_Max",
  t_min: "T_Min",
  t_max: "T_Max",
  dr_min: "DR_Min",
  dr_max: "DR_Max",
  young_modulus: "MP",
  sensitivity: "SN",
  reproducibility: "RP",
  response_time: "TR",
  stability: "ST",
  lod: "LOD",
  durability: "HL",
  power_consumption: "PC",
}

const COMBINATION_FIELD_MAP: Record<keyof SensorCombination, string> = {
  id: "Combo_ID",
  ta_id: "TA_ID",
  bre_id: "BRE_ID",
  im_id: "IM_ID",
  mem_id: "MEM_ID",
  score: "Score",
  createdAt: "created_at",
}

/**
 * Convert frontend object to backend format
 */
function toBackendFormat<T>(obj: T, fieldMap: Record<string, string>): Record<string, any> {
  const result: Record<string, any> = {}
  for (const [frontendKey, backendKey] of Object.entries(fieldMap)) {
    const value = (obj as any)[frontendKey]
    if (value !== undefined) {
      result[backendKey] = value
    }
  }
  return result
}

/**
 * Convert backend object to frontend format
 */
function fromBackendFormat<T>(obj: Record<string, any>, fieldMap: Record<string, string>): Partial<T> {
  const result: Record<string, any> = {}
  for (const [frontendKey, backendKey] of Object.entries(fieldMap)) {
    const value = obj[backendKey]
    if (value !== undefined) {
      result[frontendKey] = value
    }
  }
  return result as Partial<T>
}

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

export interface AHPResponse {
  weights: number[]
  CI: number
  CR: number
  is_consistent: boolean
}

export interface MCDARecord {
  [key: string]: any
}

export interface TopsisResultItem {
  structure: MCDARecord
  score: number
}

export interface StabilityResult {
  [structureId: string]: {
    rank_distribution: number[]
    stability_label: string
    mean_rank: number
  }
}

export interface SensitivityResult {
  [structureId: string]: {
    rank_change: number
    flags: string[]
    baseline_rank: number
    adjusted_rank: number
  }
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

const AUTH_TOKEN_STORAGE_KEY = "biosensor_access_token"
const AUTH_USERNAME_STORAGE_KEY = "biosensor_auth_username"
const AUTH_PASSWORD_STORAGE_KEY = "biosensor_auth_password"

function getBrowserStorage() {
  if (typeof window === "undefined") {
    return null
  }
  return window.localStorage
}

function getStoredToken(): string | null {
  return getBrowserStorage()?.getItem(AUTH_TOKEN_STORAGE_KEY) ?? null
}

function setStoredToken(token: string | null) {
  const storage = getBrowserStorage()
  if (!storage) return
  if (token) {
    storage.setItem(AUTH_TOKEN_STORAGE_KEY, token)
  } else {
    storage.removeItem(AUTH_TOKEN_STORAGE_KEY)
  }
}

function getStoredCredentials() {
  const storage = getBrowserStorage()
  if (!storage) return null
  const username = storage.getItem(AUTH_USERNAME_STORAGE_KEY) || process.env.NEXT_PUBLIC_AUTH_USERNAME || "admin"
  const password = storage.getItem(AUTH_PASSWORD_STORAGE_KEY) || process.env.NEXT_PUBLIC_AUTH_PASSWORD || "admin"
  return { username, password }
}

async function loginAndStoreToken(): Promise<string | null> {
  const credentials = getStoredCredentials()
  if (!credentials) return null

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(credentials),
    })

    if (!response.ok) {
      return null
    }

    const payload = await response.json()
    const token = payload?.access_token
    if (typeof token === "string" && token.length > 0) {
      setStoredToken(token)
      return token
    }
  } catch {
    // Ignore and fall back to unauthenticated request handling.
  }

  return null
}

async function buildRequestHeaders(options: RequestInit = {}, retry = false): Promise<Headers> {
  const headers = new Headers(options.headers || {})

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }

  if (!retry) {
    const token = getStoredToken()
    if (token) {
      headers.set("Authorization", `Bearer ${token}`)
    }
  }

  return headers
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
    const headers = await buildRequestHeaders(options)
    let response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok && response.status === 401 && !options.method?.toString().toUpperCase().includes("POST") && !endpoint.includes("/api/auth/login")) {
      const token = await loginAndStoreToken()
      if (token) {
        const retryHeaders = await buildRequestHeaders(options, true)
        retryHeaders.set("Authorization", `Bearer ${token}`)
        response = await fetch(url, {
          ...options,
          headers: retryHeaders,
        })
      }
    }

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
  const backendData = await fetchApi<any[]>(`${API_ENDPOINTS.analytes}?limit=${limit}&offset=${offset}`)
  return backendData.map(item => fromBackendFormat<Analyte>(item, ANALYTE_FIELD_MAP) as Analyte)
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
  const backendData = await fetchApi<any[]>(`${API_ENDPOINTS.bioRecognition}?limit=${limit}&offset=${offset}`)
  return backendData.map(item => fromBackendFormat<BioRecognitionLayer>(item, BIO_RECOGNITION_FIELD_MAP) as BioRecognitionLayer)
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
  const backendData = await fetchApi<any[]>(`${API_ENDPOINTS.immobilization}?limit=${limit}&offset=${offset}`)
  return backendData.map(item => fromBackendFormat<ImmobilizationLayer>(item, IMMOBILIZATION_FIELD_MAP) as ImmobilizationLayer)
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
  const backendData = await fetchApi<any[]>(`${API_ENDPOINTS.memristive}?limit=${limit}&offset=${offset}`)
  return backendData.map(item => fromBackendFormat<MemristiveLayer>(item, MEMRISTIVE_FIELD_MAP) as MemristiveLayer)
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
  const backendData = await fetchApi<any[]>(`${API_ENDPOINTS.combinations}?limit=${limit}&offset=${offset}`)
  return backendData.map(item => fromBackendFormat<SensorCombination>(item, COMBINATION_FIELD_MAP) as SensorCombination)
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

export async function getAHPWeights(matrix = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]): Promise<AHPResponse> {
  return fetchApi(API_ENDPOINTS.analyticsAHP, {
    method: "POST",
    body: JSON.stringify({ matrix }),
  })
}

export async function getParetoFrontier(criteria = "LoD,ST", limit = 10): Promise<MCDARecord[]> {
  return fetchApi(`${API_ENDPOINTS.analyticsPareto}?criteria=${encodeURIComponent(criteria)}&limit=${limit}`)
}

export async function getTopsisRanking(limit = 10): Promise<TopsisResultItem[]> {
  return fetchApi(`${API_ENDPOINTS.analyticsTopsis}?limit=${limit}`)
}

export async function getEpsilonConstraints(
  objective = "SN_total",
  constraints = { LoD: ["<", 10], TR: ["<", 30] },
  limit = 10
): Promise<MCDARecord[]> {
  return fetchApi(API_ENDPOINTS.analyticsEpsilonConstraints, {
    method: "POST",
    body: JSON.stringify({ objective, constraints, limit }),
  })
}

export async function getStabilityAnalysis(topK = 10, nSimulations = 1000): Promise<StabilityResult> {
  return fetchApi(`${API_ENDPOINTS.analyticsStability}?top_k=${topK}&n_simulations=${nSimulations}`)
}

export async function getSensitivityAnalysis(): Promise<SensitivityResult> {
  return fetchApi(API_ENDPOINTS.analyticsSensitivity)
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
