# Branch Protection Rules

## Для ветки `main`:

### Required status checks
- ✅ `Unit Tests` (ci-unit-tests.yml)
- ✅ `Integration Tests` (ci-integration.yml)
- ✅ `Docker Build & Smoke Tests` (ci-docker-build.yml)

### Required pull request reviews
- ✅ Minimum 1 approval
- ✅ Dismiss stale reviews when new commits are pushed
- ✅ Require conversation resolution

### Other settings
- ✅ Require branches to be up to date before merging
- ✅ Include administrators
- ❌ Do not allow force pushes
- ❌ Do not allow deletions

## Для ветки `dev`:

### Required status checks
- ✅ `Unit Tests` (ci-unit-tests.yml)
- ✅ `Integration Tests` (ci-integration.yml)

### Required pull request reviews
- ✅ Minimum 1 approval

### Other settings
- ✅ Require branches to be up to date before merging
- ❌ Do not allow force pushes

## Настройка в GitHub:

1. Перейти в Settings → Branches
2. Click "Add rule"
3. Branch name pattern: `main`
4. Включить настройки выше
5. Повторить для `dev`
