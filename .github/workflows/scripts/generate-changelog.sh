#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

VERSION="${1:-${GITHUB_REF_NAME:-}}"
if [ -z "$VERSION" ]; then
  echo "No version specified" >&2
  exit 1
fi

VERSION_VALUE="${VERSION#v}"
VERSION_VALUE="${VERSION_VALUE%-desktop}"

if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG="$(git describe --tags --abbrev=0)"
  COMMITS="$(git log --pretty=format:'- %s (%h)' "$LAST_TAG"..HEAD)"
else
  COMMITS="$(git log --pretty=format:'- %s (%h)')"
fi

if [ -z "$COMMITS" ]; then
  COMMITS="- Initial portable release"
fi

cat > desktop/CHANGELOG.txt <<EOF
## [$VERSION_VALUE] - $(date -u +%F)

### Added
- Portable Windows desktop release
- FastAPI backend packaged with PyInstaller
- Next.js frontend static assets included
- SQLite persistence in the data directory

### Fixed
- N/A

### Changed
- N/A

### Commits
$COMMITS
EOF

echo "Generated desktop/CHANGELOG.txt"
