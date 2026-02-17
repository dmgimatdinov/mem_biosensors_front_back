/**
 * API Configuration for Backend Integration
 * Centralizes all API endpoints and configuration
 */

// API Base URL - defaults to localhost for development
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
  // Health check
  health: "/api/health",
  
  // Analytes
  analytes: "/api/analytes",
  
  // Bio Recognition Layers
  bioRecognition: "/api/bio-recognition",
  
  // Immobilization Layers
  immobilization: "/api/immobilization",
  
  // Memristive Layers
  memristive: "/api/memristive",
  
  // Combinations
  combinations: "/api/combinations",
  combinationsSynthesize: "/api/combinations/synthesize",
  
  // Analytics
  analyticsStatistics: "/api/analytics/statistics",
  analyticsBestCombinations: "/api/analytics/best-combinations",
  analyticsComparative: "/api/analytics/comparative",
  
  // Export
  exportTable: (tableName: string, format: string) => `/api/export/${tableName}?format=${format}`,
  exportAll: (format: string) => `/api/export/all?format=${format}`,
} as const

/**
 * API Request configuration
 */
export const API_CONFIG = {
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
  },
} as const
