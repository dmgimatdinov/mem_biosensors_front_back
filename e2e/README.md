# E2E tests

Playwright tests for the full browser flow against the Dockerized application running on `http://localhost:80`.

## Layout

- `tests/test_navigation.spec.ts` checks sidebar navigation and core actions.
- `tests/test_api_connectivity.spec.ts` checks backend reachability and API responses.
- `tests/test_full_flow.spec.ts` creates a passport, verifies persistence, and runs synthesis.

## Run

1. Start the application stack so the frontend is available on port `80`.
2. Install dependencies inside `e2e/`.
3. Install the Chromium browser once with `npm run install:browsers`.
4. Run `npm test`.

### Environment

- `E2E_BASE_URL` overrides the default `http://localhost:80` target.
- `PLAYWRIGHT_BASE_URL` is also supported for compatibility.

## Notes

- These tests do not start a local dev server.
- They expect the frontend to proxy API requests to the running FastAPI backend.
- The save flow uses unique IDs so repeated runs do not collide with existing data.