import { defineConfig, devices } from "@playwright/test"

const baseURL = process.env.E2E_BASE_URL ?? process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:80"
const dockerComposeFile = "/workspaces/mem_biosensors_front_back/docker-compose.yml"

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },
  reporter: [
    ["html", { open: "never" }],
    ["list"],
    ["junit", { outputFile: "test-results/junit.xml" }],
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: `docker compose -f ${dockerComposeFile} up --build app`,
    url: `${baseURL}/api/health`,
    timeout: 240_000,
    reuseExistingServer: !process.env.CI,
  },
})