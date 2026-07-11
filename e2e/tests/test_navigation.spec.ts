import { expect, test } from "@playwright/test"

const sections = [
  { label: "Data Entry", heading: "Data Entry", action: /Save Passport/ },
  { label: "Database", heading: "Database", action: /Page 1 of/ },
  { label: "Analysis", heading: "Analysis & Synthesis", action: /Run Synthesis/ },
  { label: "Export", heading: "Export Data", action: /Export CSV/ },
] as const

test("sidebar navigation switches between app sections", async ({ page }) => {
  await page.goto("/")
  await page.waitForLoadState("networkidle")
  await expect(page.getByRole("heading", { name: "Data Entry" })).toBeVisible({ timeout: 30_000 })

  for (const section of sections) {
    await page.getByRole("navigation").getByRole("button", { name: section.label }).click()
    await expect(page.getByRole("heading", { name: section.heading })).toBeVisible()
    await expect(page.getByText(section.action)).toBeVisible()
  }
})

test("sidebar exposes the primary actions used in the Docker build", async ({ page }) => {
  await page.goto("/")

  const sidebar = page.locator("aside")

  await expect(sidebar.getByRole("button", { name: "Save", exact: true }).first()).toBeVisible()
  await expect(sidebar.getByRole("button", { name: "Load", exact: true }).first()).toBeVisible()
  await expect(sidebar.getByRole("button", { name: "Clear", exact: true }).first()).toBeVisible()
  await expect(sidebar.getByRole("button", { name: "Export", exact: true }).last()).toBeVisible()
})