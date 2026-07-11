import { expect, test } from "@playwright/test"

function uniqueId(prefix: string) {
  const timestamp = Date.now().toString(36).toUpperCase().slice(-6)
  const randomPart = Math.floor(Math.random() * 1_000).toString(36).toUpperCase().padStart(3, "0")
  return `${prefix}${timestamp}${randomPart}`
}

const skipUiE2E = process.env.SKIP_UI_E2E === "true"

test.skip(skipUiE2E, "UI E2E is temporarily skipped in CI until frontend runtime is fully containerized")

test("user can create a passport and run synthesis end to end", async ({ page, request }) => {
  const analyteId = uniqueId("TA")
  const breId = uniqueId("BRE")
  const imId = uniqueId("IM")
  const memId = uniqueId("MEM")

  await page.goto("/")
  await page.waitForLoadState("networkidle")
  await expect(page.getByRole("heading", { name: "Data Entry" })).toBeVisible({ timeout: 30_000 })

  await page.getByPlaceholder("TA001").fill(analyteId)
  await page.getByPlaceholder("Glucose").fill("E2E Analyte")
  await page.getByPlaceholder("BRE001").fill(breId)
  await page.getByPlaceholder("GOx Enzyme").fill("E2E BRE")
  await page.getByPlaceholder("IM001").fill(imId)
  await page.getByPlaceholder("SAM-Au").fill("E2E IM")
  await page.getByPlaceholder("MEM001").fill(memId)
  await page.getByPlaceholder("TiO2 Memristor").fill("E2E MEM")

  await page.getByRole("button", { name: "Save Passport" }).click()

  await expect
    .poll(async () => {
      const analytesResponse = await request.get("/api/analytes?limit=1000&offset=0")
      const bioResponse = await request.get("/api/bio-recognition?limit=1000&offset=0")
      const imResponse = await request.get("/api/immobilization?limit=1000&offset=0")
      const memResponse = await request.get("/api/memristive?limit=1000&offset=0")

      if (!analytesResponse.ok() || !bioResponse.ok() || !imResponse.ok() || !memResponse.ok()) {
        return false
      }

      const analytes = await analytesResponse.json()
      const bioRecognitions = await bioResponse.json()
      const immobilizations = await imResponse.json()
      const memristives = await memResponse.json()

      return (
        analytes.some((item: { TA_ID?: string }) => item.TA_ID === analyteId) &&
        bioRecognitions.some((item: { BRE_ID?: string }) => item.BRE_ID === breId) &&
        immobilizations.some((item: { IM_ID?: string }) => item.IM_ID === imId) &&
        memristives.some((item: { MEM_ID?: string }) => item.MEM_ID === memId)
      )
    }, { timeout: 30_000 })
    .toBe(true)

  await page.getByRole("button", { name: "Database" }).click()
  await expect(page.getByRole("heading", { name: "Database" })).toBeVisible()

  await page.getByRole("button", { name: "Analysis" }).click()
  await expect(page.getByRole("heading", { name: "Analysis & Synthesis" })).toBeVisible()

  await page.getByRole("button", { name: "Run Synthesis" }).click()
  await expect(page.getByText(/Synthesis complete:/)).toBeVisible({ timeout: 30_000 })

  const topCombinationsHeading = page.getByRole("heading", { name: /Top \d+ Combinations by Score/ })
  const noCombinationsHint = page.getByText("No combinations to visualize. Run synthesis first.")
  await expect(topCombinationsHeading.or(noCombinationsHint)).toBeVisible()
})