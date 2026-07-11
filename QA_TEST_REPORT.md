# QA Test Report

## Scope

Validation after E2E + frontend/backend integration fixes for Dockerized run on port 80.

## Environment

- Date: 2026-07-11
- Repository: `dmgimatdinov/mem_biosensors_front_back`
- Branch: `dev-feat`

## Backend Test Matrix (Prompts 1-9)

| Suite | Result | Notes |
|---|---:|---|
| smoke | 22 passed | 2 warnings |
| unit | 99 passed, 3 skipped | 2 warnings |
| integration | 78 passed, 13 skipped | 2 warnings |
| contract | 22 passed | 2 warnings |
| security | 33 passed, 1 skipped | 2 warnings |
| performance | 15 passed | 2 warnings |

Backend totals:
- Passed: 269
- Skipped: 17

## E2E Test Suite

Command:

```bash
cd e2e
npm test
```

Result:
- 7 passed
- Duration: 22.4s

Covered specs:
- `e2e/tests/test_api_connectivity.spec.ts`
- `e2e/tests/test_navigation.spec.ts`
- `e2e/tests/test_full_flow.spec.ts`

## Remarks

- E2E is executed against real Dockerized app startup via Playwright `webServer` and health readiness.
- Test-generated artifacts (`e2e/playwright-report`, `e2e/test-results`) are excluded from commit.
