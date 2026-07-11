import { expect, test } from "@playwright/test"

function uniqueId(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.floor(Math.random() * 10000)}`
}

test("user can create a passport and run synthesis end to end", async ({ page, request }) => {
  const analyteId = uniqueId("TAE2E")
  const breId = uniqueId("BREE2E")
  const imId = uniqueId("IME2E")
  const memId = uniqueId("MEME2E")

  await page.goto("/")
  await expect(page.getByRole("heading", { name: "Data Entry" })).toBeVisible()

  await page.getByLabel("Analyte ID").fill(analyteId)
  await page.getByLabel("Name").nth(0).fill("E2E Analyte")
  await page.getByLabel("BRE ID").fill(breId)
  await page.getByLabel("Name").nth(1).fill("E2E BRE")
  await page.getByLabel("IM ID").fill(imId)
  await page.getByLabel("Name").nth(2).fill("E2E IM")
  await page.getByLabel("MEM ID").fill(memId)
  await page.getByLabel("Name").nth(3).fill("E2E MEM")

  await page.getByRole("button", { name: "Save Passport" }).click()
  await expect(page.getByText("All layers saved successfully to database")).toBeVisible()

  const analytesResponse = await request.get("/api/analytes?limit=200&offset=0")
  const bioResponse = await request.get("/api/bio-recognition?limit=200&offset=0")
  const imResponse = await request.get("/api/immobilization?limit=200&offset=0")
  const memResponse = await request.get("/api/memristive?limit=200&offset=0")

  expect(analytesResponse.ok()).toBeTruthy()
  expect(bioResponse.ok()).toBeTruthy()
  expect(imResponse.ok()).toBeTruthy()
  expect(memResponse.ok()).toBeTruthy()

  const analytes = await analytesResponse.json()
  const bioRecognitions = await bioResponse.json()
  const immobilizations = await imResponse.json()
  const memristives = await memResponse.json()

  expect(analytes.some((item: { TA_ID?: string }) => item.TA_ID === analyteId)).toBe(true)
  expect(bioRecognitions.some((item: { BRE_ID?: string }) => item.BRE_ID === breId)).toBe(true)
  expect(immobilizations.some((item: { IM_ID?: string }) => item.IM_ID === imId)).toBe(true)
  expect(memristives.some((item: { MEM_ID?: string }) => item.MEM_ID === memId)).toBe(true)

  await page.getByRole("button", { name: "Analysis" }).click()
  await expect(page.getByRole("heading", { name: "Analysis & Synthesis" })).toBeVisible()

  await page.getByRole("button", { name: "Run Synthesis" }).click()
  await expect(page.getByText(/Synthesis complete:/)).toBeVisible()
  await expect(page.getByRole("heading", { name: /Top \d+ Combinations by Score/ })).toBeVisible()
})