# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps

COPY frontend/ .
RUN npm run build

# Stage 2: Backend + pre-built frontend
FROM python:3.11-slim

# Install only git (runtime, no Node.js needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache layer: install Python dependencies first (before copying source)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy pre-built frontend from stage 1
COPY --from=frontend-builder /frontend/out ./frontend/out

# Copy startup script and .env
COPY start.sh ./start.sh
RUN chmod +x start.sh

EXPOSE 8000 3000
CMD ["./start.sh"]
