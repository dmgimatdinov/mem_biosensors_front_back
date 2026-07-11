# E2E Tests

Playwright tests for the full browser flow against the Dockerized application running on `http://localhost:80`.

## What is covered

- `tests/test_navigation.spec.ts` checks sidebar navigation and the main SPA sections.
- `tests/test_api_connectivity.spec.ts` checks backend reachability, list endpoints, creation, and CORS.
- `tests/test_full_flow.spec.ts` creates a passport, verifies persistence, and runs synthesis.

## Requirements

- Node.js 20+
- Docker
- Playwright 1.40+

## Install

```bash
cd e2e
npm install
npm run install:browsers
```

## Run

`npm test` starts the Dockerized app through the Playwright web server hook, waits for port `80`, and then runs the browser tests.

### Local commands

```bash
npm test
npm run test:headed
npm run test:debug
npm run test:ui
npm run test:chromium
npm run test:report
```

## Environment

- `E2E_BASE_URL` overrides the default `http://localhost:80` target.
- `PLAYWRIGHT_BASE_URL` is also supported for compatibility.

## Notes

- The suite uses the real nginx proxy and FastAPI backend inside Docker.
- Test data is synthetic and uses unique IDs to avoid collisions across repeated runs.
- The tests avoid destructive cleanup, so the container lifecycle is expected to provide isolation.