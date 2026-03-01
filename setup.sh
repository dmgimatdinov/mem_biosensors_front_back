#!/usr/bin/env bash
# =============================================================================
# setup.sh — Bootstrap a fresh Ubuntu machine for mem_biosensors_front_back
#
# What this script does:
#   1. Updates apt and installs system prerequisites
#   2. Installs Python 3 + pip + venv
#   3. Installs Node.js LTS (via NodeSource) + npm
#   4. Creates a Python virtual environment at ./backend/.venv and activates it
#   5. Installs all Python dependencies from backend/requirements.txt
#   6. Installs all Node.js dependencies from frontend/package.json
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh            # run as root or with sudo
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_ROOT/backend/.venv"
NODE_MAJOR=20   # Node.js LTS major version

# ─── Colour helpers ──────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
info()  { echo -e "${GREEN}[setup] $*${RESET}"; }
warn()  { echo -e "${YELLOW}[setup] $*${RESET}"; }
error() { echo -e "${RED}[setup] ERROR: $*${RESET}" >&2; exit 1; }

# ─── 1. System prerequisites ─────────────────────────────────────────────────
info "Updating package lists…"
apt-get update -y

info "Installing system prerequisites (curl, git, build-essential, ca-certificates)…"
apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    git \
    build-essential \
    gcc \
    g++

# ─── 2. Python ───────────────────────────────────────────────────────────────
info "Installing Python 3, pip, and venv…"
apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev

# Ensure 'python3' is available as 'python' (convenience alias)
if ! command -v python &>/dev/null; then
    apt-get install -y --no-install-recommends python-is-python3 2>/dev/null || \
        update-alternatives --install /usr/bin/python python "$(command -v python3)" 1
fi

info "Python version: $(python3 --version)"

# ─── 3. Node.js ──────────────────────────────────────────────────────────────
if command -v node &>/dev/null; then
    warn "Node.js $(node --version) already installed — skipping NodeSource setup."
else
    info "Adding NodeSource repository for Node.js ${NODE_MAJOR}.x…"
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash -
    apt-get install -y --no-install-recommends nodejs
fi

info "Node.js version: $(node --version)"
info "npm version:     $(npm --version)"

# ─── 4. Python virtual environment ───────────────────────────────────────────
info "Creating Python virtual environment at $VENV_DIR…"
python3 -m venv "$VENV_DIR"

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
info "Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip inside the venv
pip install --upgrade pip

# ─── 5. Python dependencies ──────────────────────────────────────────────────
info "Installing Python dependencies from backend/requirements.txt…"
pip install -r "$REPO_ROOT/backend/requirements.txt"

info "Python packages installed:"
pip list

# ─── 6. Node.js dependencies ─────────────────────────────────────────────────
info "Installing Node.js dependencies in frontend/…"
cd "$REPO_ROOT/frontend"
npm install
cd "$REPO_ROOT"

info "Node.js packages installed."

# ─── Done ────────────────────────────────────────────────────────────────────
echo ""
info "==================================================================="
info " All dependencies installed successfully!"
info ""
info " To activate the Python virtual environment in your shell, run:"
info "   source $VENV_DIR/bin/activate"
info ""
info " To start the backend (FastAPI):"
info "   cd backend && uvicorn main:app --reload"
info ""
info " To start the frontend (Next.js dev server):"
info "   cd frontend && npm run dev"
info "==================================================================="
