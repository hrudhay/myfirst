#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

# Verify ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ERROR: ANTHROPIC_API_KEY environment variable is not set."
  echo "  export ANTHROPIC_API_KEY=your_key_here"
  exit 1
fi

# Create and activate virtual environment if needed
if [ ! -d "$BACKEND_DIR/.venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv "$BACKEND_DIR/.venv"
fi

source "$BACKEND_DIR/.venv/bin/activate"

# Install dependencies
echo "Installing backend dependencies..."
pip install -q -r "$BACKEND_DIR/requirements.txt"

echo ""
echo "  Restaurant Inventory System"
echo "  ─────────────────────────────────────────"
echo "  Backend API : http://localhost:8000"
echo "  API Docs    : http://localhost:8000/docs"
echo "  Frontend    : open frontend/index.html in your browser"
echo "  ─────────────────────────────────────────"
echo ""

cd "$BACKEND_DIR"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
