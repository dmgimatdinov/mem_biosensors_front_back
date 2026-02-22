# ============================================================
# Multi-stage Dockerfile for mem_biosensors_front_back
# Result: ONE image running nginx (port 80) + FastAPI (port 8080)
#   • GET /        → nginx serves Next.js static SPA
#   • GET /api/*   → nginx proxies to uvicorn on localhost:8080
# ============================================================

# ── Stage 1: Build the Next.js frontend ──────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Install dependencies first (cached layer)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci 

# Copy source and build a static export
COPY frontend/ .

# At build-time the SPA will call /api/* which nginx proxies locally,
# so the public API URL is an empty string (same-origin).
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build
# Output: /frontend/out  (Next.js static export)


# ── Stage 2: Install Python dependencies ─────────────────────
FROM python:3.11-slim AS backend-builder

WORKDIR /deps

COPY backend/requirements.txt .

# Install build tools needed for some C-extension wheels,
# then install all Python packages into a prefix we can copy later.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ git \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt \
    && apt-get purge -y gcc g++ \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*


# ── Stage 3: Final image ──────────────────────────────────────
FROM python:3.11-slim

# Install nginx, supervisor, and wget (wget is used by the docker-compose healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx \
        supervisor \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from the builder stage
COPY --from=backend-builder /install /usr/local

# Copy FastAPI application code
COPY backend/ /app
WORKDIR /app

# Copy the Next.js static export into the nginx web root
COPY --from=frontend-builder /frontend/out /usr/share/nginx/html

# Replace the default nginx site config with our custom proxy config
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Remove the default nginx config to avoid conflicts
RUN rm -f /etc/nginx/sites-enabled/default

# Copy supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ── Environment variables for the backend ─────────────────────
# Override these at runtime via -e / docker-compose environment section
ENV DATABASE_URL=sqlite:///./memristive_biosensor.db \
    LOG_LEVEL=INFO \
    WORKERS=1

# Only port 80 (nginx) needs to be published; port 8080 is internal
EXPOSE 80

# Launch both nginx and uvicorn through supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
