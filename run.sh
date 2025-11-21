#!/bin/bash

# Diagnosaurus.ai Run Script
# Quick start for development

set -e

echo "🦖 Starting Diagnosaurus.ai..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if Redis is running
if ! docker ps | grep -q diagnosaurus-redis; then
    echo "Starting Redis..."
    docker-compose up -d
    sleep 3
fi

# Check .env
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "Please edit .env with your API keys before running."
    exit 1
fi

# Run Flask app
echo "✓ Starting Flask application..."
echo "✓ Visit http://localhost:5000"
echo ""
python app.py
