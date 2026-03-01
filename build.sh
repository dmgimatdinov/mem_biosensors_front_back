#!/usr/bin/env bash
# Monolithic build script for Cloudflare Pages deployment
# Builds Next.js static export and bundles the FastAPI backend into dist/

set -euo pipefail

echo "==> Building Next.js frontend..."
cd frontend
npm ci
npm run build
cd ..

echo "==> Copying Next.js static export to dist/..."
rm -rf dist
cp -r frontend/out dist

echo "==> Copying FastAPI backend to dist/api/..."
mkdir -p dist/api
cp -r backend/* dist/api/

echo "==> Installing Python dependencies into dist/api/..."
pip install \
    --ignore-installed \
    --target dist/api \
    -r backend/requirements.txt

echo "==> Build complete. Output directory: dist/"
