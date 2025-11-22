#!/bin/bash

set -eou pipefail

. _actvenv.sh

# Check if Flask is installed
python -c "import flask" 2>/dev/null || {
    echo "Flask not installed. Run ./_install.sh first" > /dev/stderr
    exit 1
}

# Check .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env not found. Creating from template..."
    cp .env.example .env
    echo "Edit .env with your API keys before running."
    exit 1
fi

# Start Redis if not running
if ! docker ps | grep -q diagnosaurus-redis; then
    echo "Starting Redis..."
    docker-compose up -d
    sleep 2
fi

PORT=$(python -c "from config import settings; print(settings.port)" 2>/dev/null || echo "5000")
echo "🦖 Starting Diagnosaurus.ai on http://localhost:${PORT}"
python app.py
