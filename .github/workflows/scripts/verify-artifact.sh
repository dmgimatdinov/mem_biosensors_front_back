#!/usr/bin/env bash
set -euo pipefail

ARTIFACT_PATH="${1:-}"
if [ -z "$ARTIFACT_PATH" ]; then
  echo "Artifact path is required" >&2
  exit 1
fi

if [ ! -f "$ARTIFACT_PATH" ]; then
  echo "Artifact not found: $ARTIFACT_PATH" >&2
  exit 1
fi

SIZE_BYTES=$(wc -c < "$ARTIFACT_PATH")
if [ "$SIZE_BYTES" -lt 1000000 ]; then
  echo "Artifact is suspiciously small: ${SIZE_BYTES} bytes" >&2
  exit 1
fi

if ! command -v sha256sum >/dev/null 2>&1; then
  echo "sha256sum is required" >&2
  exit 1
fi

sha256sum "$ARTIFACT_PATH"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

unzip -q "$ARTIFACT_PATH" -d "$TMP_DIR"
find "$TMP_DIR" -maxdepth 2 -type f | sort

if ! find "$TMP_DIR" -type f | grep -q 'mem_biosensors.exe'; then
  echo "mem_biosensors.exe was not found inside the archive" >&2
  exit 1
fi

echo "Artifact verification completed"
