import { expect, test } from "@playwright/test"

test("backend health endpoint is reachable through the Docker runtime", async ({ request }) => {
  const response = await request.get("/api/health")

  expect(response.ok()).toBeTruthy()

  const payload = await response.json()
  expect(payload).toMatchObject({
    status: expect.any(String),
    message: expect.any(String),
  })
})

test("frontend can fetch the main API collections", async ({ request }) => {
  const endpoints = [
    "/api/analytes?limit=1&offset=0",
    "/api/bio-recognition?limit=1&offset=0",
    "/api/immobilization?limit=1&offset=0",
    "/api/memristive?limit=1&offset=0",
    "/api/combinations?limit=1&offset=0",
    "/api/analytics/statistics",
  ]

  for (const endpoint of endpoints) {
    const response = await request.get(endpoint)
    expect(response.ok(), endpoint).toBeTruthy()
  }
})