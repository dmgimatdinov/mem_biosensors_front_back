// Types for biosensor passport data
export interface Analyte {
  ta_id: string
  ta_name: string
  ph_min: number
  ph_max: number
  t_max: number
  stability: number
  half_life: number
  power_consumption: number
}

export interface BioRecognitionLayer {
  bre_id: string
  bre_name: string
  ph_min: number
  ph_max: number
  t_min: number
  t_max: number
  dr_min: number
  dr_max: number
  sensitivity: number
  reproducibility: number
  response_time: number
  stability: number
  lod: number
  durability: number
  power_consumption: number
}

export interface ImmobilizationLayer {
  im_id: string
  im_name: string
  ph_min: number
  ph_max: number
  t_min: number
  t_max: number
  young_modulus: number
  adhesion: string
  solubility: string
  loss_coefficient: number
  reproducibility: number
  response_time: number
  stability: number
  durability: number
  power_consumption: number
}

export interface MemristiveLayer {
  mem_id: string
  mem_name: string
  ph_min: number
  ph_max: number
  t_min: number
  t_max: number
  dr_min: number
  dr_max: number
  young_modulus: number
  sensitivity: number
  reproducibility: number
  response_time: number
  stability: number
  lod: number
  durability: number
  power_consumption: number
}

export interface Passport {
  analyte: Analyte
  bioRecognition: BioRecognitionLayer
  immobilization: ImmobilizationLayer
  memristive: MemristiveLayer
  createdAt: string
}

export interface SensorCombination {
  id: string
  ta_id: string
  bre_id: string
  im_id: string
  mem_id: string
  score: number
  createdAt: string
}

// Default empty structures
export function emptyAnalyte(): Analyte {
  return {
    ta_id: "",
    ta_name: "",
    ph_min: 2.0,
    ph_max: 10.0,
    t_max: 37,
    stability: 30,
    half_life: 24,
    power_consumption: 100,
  }
}

export function emptyBioRecognition(): BioRecognitionLayer {
  return {
    bre_id: "",
    bre_name: "",
    ph_min: 2.0,
    ph_max: 10.0,
    t_min: 4,
    t_max: 37,
    dr_min: 1,
    dr_max: 1000,
    sensitivity: 100,
    reproducibility: 95,
    response_time: 60,
    stability: 30,
    lod: 10,
    durability: 1000,
    power_consumption: 50,
  }
}

export function emptyImmobilization(): ImmobilizationLayer {
  return {
    im_id: "",
    im_name: "",
    ph_min: 2.0,
    ph_max: 10.0,
    t_min: 4,
    t_max: 80,
    young_modulus: 10,
    adhesion: "medium",
    solubility: "low",
    loss_coefficient: 0.1,
    reproducibility: 90,
    response_time: 120,
    stability: 60,
    durability: 5000,
    power_consumption: 10,
  }
}

export function emptyMemristive(): MemristiveLayer {
  return {
    mem_id: "",
    mem_name: "",
    ph_min: 2.0,
    ph_max: 10.0,
    t_min: 5,
    t_max: 85,
    dr_min: 0.001,
    dr_max: 100000,
    young_modulus: 50,
    sensitivity: 100,
    reproducibility: 92,
    response_time: 30,
    stability: 90,
    lod: 5,
    durability: 10000,
    power_consumption: 20,
  }
}

// In-memory data store (client-side state management)
const STORAGE_KEY = "biosensor_data"

export interface StoreData {
  analytes: Analyte[]
  bioRecognitions: BioRecognitionLayer[]
  immobilizations: ImmobilizationLayer[]
  memristives: MemristiveLayer[]
  combinations: SensorCombination[]
  passports: Passport[]
}

function getDefaultData(): StoreData {
  return {
    analytes: [
      { ta_id: "TA001", ta_name: "Glucose", ph_min: 4.0, ph_max: 8.0, t_max: 45, stability: 180, half_life: 720, power_consumption: 50 },
      { ta_id: "TA002", ta_name: "Dopamine", ph_min: 6.0, ph_max: 8.5, t_max: 37, stability: 90, half_life: 48, power_consumption: 75 },
      { ta_id: "TA003", ta_name: "Cortisol", ph_min: 5.0, ph_max: 9.0, t_max: 40, stability: 120, half_life: 168, power_consumption: 60 },
    ],
    bioRecognitions: [
      { bre_id: "BRE001", bre_name: "GOx Enzyme", ph_min: 4.0, ph_max: 7.5, t_min: 10, t_max: 60, dr_min: 0.5, dr_max: 50000, sensitivity: 12500, reproducibility: 97, response_time: 15, stability: 90, lod: 5, durability: 5000, power_consumption: 25 },
      { bre_id: "BRE002", bre_name: "Aptamer-D1", ph_min: 6.0, ph_max: 8.0, t_min: 15, t_max: 45, dr_min: 1.0, dr_max: 10000, sensitivity: 8000, reproducibility: 92, response_time: 30, stability: 60, lod: 2, durability: 3000, power_consumption: 30 },
    ],
    immobilizations: [
      { im_id: "IM001", im_name: "SAM-Au", ph_min: 3.0, ph_max: 9.0, t_min: 5, t_max: 100, young_modulus: 78, adhesion: "high", solubility: "low", loss_coefficient: 0.05, reproducibility: 96, response_time: 5, stability: 180, durability: 20000, power_consumption: 5 },
      { im_id: "IM002", im_name: "Chitosan Film", ph_min: 4.0, ph_max: 8.0, t_min: 10, t_max: 80, young_modulus: 3.5, adhesion: "medium", solubility: "medium", loss_coefficient: 0.15, reproducibility: 88, response_time: 10, stability: 90, durability: 8000, power_consumption: 8 },
    ],
    memristives: [
      { mem_id: "MEM001", mem_name: "TiO2 Memristor", ph_min: 3.0, ph_max: 9.0, t_min: 5, t_max: 100, dr_min: 0.0001, dr_max: 1000000, young_modulus: 230, sensitivity: 450, reproducibility: 94, response_time: 0.5, stability: 365, lod: 0.1, durability: 50000, power_consumption: 15 },
      { mem_id: "MEM002", mem_name: "HfO2 ReRAM", ph_min: 4.0, ph_max: 8.5, t_min: 10, t_max: 85, dr_min: 0.001, dr_max: 500000, young_modulus: 180, sensitivity: 320, reproducibility: 91, response_time: 1.0, stability: 270, lod: 0.5, durability: 30000, power_consumption: 20 },
    ],
    combinations: [
      { id: "COMB001", ta_id: "TA001", bre_id: "BRE001", im_id: "IM001", mem_id: "MEM001", score: 94.2, createdAt: "2026-01-15" },
      { id: "COMB002", ta_id: "TA001", bre_id: "BRE002", im_id: "IM001", mem_id: "MEM001", score: 87.5, createdAt: "2026-01-15" },
      { id: "COMB003", ta_id: "TA002", bre_id: "BRE002", im_id: "IM002", mem_id: "MEM002", score: 82.1, createdAt: "2026-01-16" },
      { id: "COMB004", ta_id: "TA001", bre_id: "BRE001", im_id: "IM002", mem_id: "MEM002", score: 79.8, createdAt: "2026-01-16" },
      { id: "COMB005", ta_id: "TA003", bre_id: "BRE001", im_id: "IM001", mem_id: "MEM002", score: 76.3, createdAt: "2026-01-17" },
      { id: "COMB006", ta_id: "TA002", bre_id: "BRE001", im_id: "IM002", mem_id: "MEM001", score: 91.0, createdAt: "2026-01-17" },
      { id: "COMB007", ta_id: "TA003", bre_id: "BRE002", im_id: "IM001", mem_id: "MEM001", score: 85.7, createdAt: "2026-01-18" },
      { id: "COMB008", ta_id: "TA003", bre_id: "BRE001", im_id: "IM002", mem_id: "MEM001", score: 72.4, createdAt: "2026-01-18" },
      { id: "COMB009", ta_id: "TA002", bre_id: "BRE001", im_id: "IM001", mem_id: "MEM002", score: 88.9, createdAt: "2026-01-19" },
      { id: "COMB010", ta_id: "TA001", bre_id: "BRE002", im_id: "IM002", mem_id: "MEM002", score: 68.5, createdAt: "2026-01-19" },
      { id: "COMB011", ta_id: "TA003", bre_id: "BRE002", im_id: "IM002", mem_id: "MEM002", score: 63.2, createdAt: "2026-01-20" },
      { id: "COMB012", ta_id: "TA002", bre_id: "BRE002", im_id: "IM002", mem_id: "MEM001", score: 74.8, createdAt: "2026-01-20" },
    ],
    passports: [],
  }
}

export function loadStore(): StoreData {
  if (typeof window === "undefined") return getDefaultData()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  const def = getDefaultData()
  localStorage.setItem(STORAGE_KEY, JSON.stringify(def))
  return def
}

export function saveStore(data: StoreData): void {
  if (typeof window === "undefined") return
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

export function synthesizeCombinations(data: StoreData): { checked: number; created: number; updatedData: StoreData } {
  const existingKeys = new Set(data.combinations.map(c => `${c.ta_id}-${c.bre_id}-${c.im_id}-${c.mem_id}`))
  let checked = 0
  let created = 0
  const newCombos: SensorCombination[] = []

  for (const ta of data.analytes) {
    for (const bre of data.bioRecognitions) {
      for (const im of data.immobilizations) {
        for (const mem of data.memristives) {
          checked++
          const key = `${ta.ta_id}-${bre.bre_id}-${im.im_id}-${mem.mem_id}`
          if (!existingKeys.has(key)) {
            // Score calculation based on parameters
            const phCompat = Math.max(0, Math.min(bre.ph_max, im.ph_max, mem.ph_max, ta.ph_max) - Math.max(bre.ph_min, im.ph_min, mem.ph_min, ta.ph_min)) / 8
            const senScore = Math.min(bre.sensitivity / 20000, 1)
            const repScore = (bre.reproducibility + im.reproducibility + mem.reproducibility) / 300
            const stabScore = (bre.stability + im.stability + mem.stability) / (365 * 3)
            const score = Math.round(((phCompat * 25 + senScore * 25 + repScore * 25 + stabScore * 25) + Math.random() * 10) * 10) / 10
            const clampedScore = Math.min(100, Math.max(0, score))

            newCombos.push({
              id: `COMB${String(data.combinations.length + newCombos.length + 1).padStart(3, "0")}`,
              ta_id: ta.ta_id,
              bre_id: bre.bre_id,
              im_id: im.im_id,
              mem_id: mem.mem_id,
              score: clampedScore,
              createdAt: new Date().toISOString().split("T")[0],
            })
            created++
          }
          if (checked >= 5000) break
        }
        if (checked >= 5000) break
      }
      if (checked >= 5000) break
    }
    if (checked >= 5000) break
  }

  const updatedData = {
    ...data,
    combinations: [...data.combinations, ...newCombos],
  }

  return { checked, created, updatedData }
}

export type TableName = "analytes" | "bioRecognitions" | "immobilizations" | "memristives" | "combinations"

export const TABLE_LABELS: Record<TableName, string> = {
  analytes: "Analytes (TA)",
  bioRecognitions: "Bio-recognition Layers (BRE)",
  immobilizations: "Immobilization Layers (IM)",
  memristives: "Memristive Layers (MEM)",
  combinations: "Sensor Combinations",
}

export const TABLE_LABELS_RU: Record<TableName, string> = {
  analytes: "Analytes (TA)",
  bioRecognitions: "Bio-Recognition (BRE)",
  immobilizations: "Immobilization (IM)",
  memristives: "Memristive (MEM)",
  combinations: "Combinations",
}
