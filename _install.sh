#!/bin/bash

set -eou pipefail

echo "🦖 Installing Diagnosaurus.ai..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker required for Redis. Install it first."
    exit 1
fi
echo "✓ Docker found"

# Ensure pyenv exists
./_ensurepyenv.sh

# Install Python version from .python-version
PY_VERS=$(cat .python-version)
if pyenv versions --bare | grep -q "^$PY_VERS\$"; then
    echo "✓ Python $PY_VERS already installed"
else
    echo "Installing Python $PY_VERS..."
    pyenv install
fi
python --version

# Create venv if needed
if [ ! -d venv ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate and install dependencies
. _actvenv.sh
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from template if missing
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Edit .env and add your API keys before running"
fi

# Create directories
mkdir -p uploads data
touch uploads/.gitkeep

# Start Redis
echo "Starting Redis (will also start it during _dev.sh, but doing it here to do the heavy lifting first associated with the initial start)..."
docker-compose up -d
sleep 2

# Verify Redis
if docker exec diagnosaurus-redis redis-cli ping | grep -q PONG; then
    echo "✓ Redis is running"
else
    echo "❌ Redis failed to start"
    exit 1
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: ./_dev.sh"
