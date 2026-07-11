import { expect, test } from "@playwright/test"

function uniqueId(prefix: string) {
  const timestamp = Date.now().toString(36).toUpperCase().slice(-6)
  const randomPart = Math.floor(Math.random() * 1_000).toString(36).toUpperCase().padStart(3, "0")
  return `${prefix}${timestamp}${randomPart}`
}

test("backend health endpoint is reachable through the Docker runtime", async ({ request }) => {
  const response = await request.get("/api/health")

  expect(response.ok()).toBeTruthy()

  const payload = await response.json()
  expect(payload).toMatchObject({
    status: "ok",
    message: expect.any(String),
  })
})

test("frontend can fetch the main API collections", async ({ request }) => {
  const endpoints = [
    "/api/analytes?limit=5&offset=0",
    "/api/bio-recognition?limit=5&offset=0",
    "/api/immobilization?limit=5&offset=0",
    "/api/memristive?limit=5&offset=0",
    "/api/combinations?limit=5&offset=0",
    "/api/analytics/statistics",
  ]

  for (const endpoint of endpoints) {
    const response = await request.get(endpoint)
    expect(response.ok(), endpoint).toBeTruthy()
  }
})

test("frontend can create and read back a unique analyte via the API", async ({ request }) => {
  const analyteId = uniqueId("TA")

  const createResponse = await request.post("/api/analytes", {
    data: {
      ta_id: analyteId,
      ta_name: "E2E API Test Analyte",
      ph_min: 5.0,
      ph_max: 8.0,
      t_max: 80,
      stability: 180,
      half_life: 4380,
      power_consumption: 500,
    },
  })

  expect(createResponse.ok()).toBeTruthy()

  const listResponse = await request.get("/api/analytes?limit=1000&offset=0")
  expect(listResponse.ok()).toBeTruthy()

  const analytes = await listResponse.json()
  expect(analytes.some((item: { TA_ID?: string }) => item.TA_ID === analyteId)).toBe(true)
})

test("API returns correct CORS headers", async ({ request }) => {
  const response = await request.get("/api/health", {
    headers: {
      Origin: "http://localhost:3000",
    },
  })

  expect(response.ok()).toBeTruthy()

  const corsHeader = response.headers()["access-control-allow-origin"]
  expect(corsHeader).toContain("localhost:3000")
})