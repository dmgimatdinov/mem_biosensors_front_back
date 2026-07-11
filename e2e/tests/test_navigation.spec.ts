import { expect, test } from "@playwright/test"

const sections = [
  { label: "Data Entry", heading: "Data Entry" },
  { label: "Database", heading: "Database" },
  { label: "Analysis", heading: "Analysis & Synthesis" },
  { label: "Export", heading: "Export Data" },
] as const

test("sidebar navigation switches between app sections", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByRole("heading", { name: "Data Entry" })).toBeVisible()

  for (const section of sections) {
    await page.getByRole("button", { name: section.label }).click()
    await expect(page.getByRole("heading", { name: section.heading })).toBeVisible()
  }
})

test("sidebar exposes the primary actions used in the Docker build", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByRole("button", { name: "Save" })).toBeVisible()
  await expect(page.getByRole("button", { name: "Load" })).toBeVisible()
  await expect(page.getByRole("button", { name: "Clear" })).toBeVisible()
  await expect(page.getByRole("button", { name: "Export" })).toBeVisible()
})