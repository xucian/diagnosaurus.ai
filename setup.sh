#!/bin/bash

# Diagnosaurus.ai Setup Script
# Quick setup for hackathon demo

set -e

echo "🦖 Diagnosaurus.ai Setup"
echo "======================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version"

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi
echo "✓ Docker installed"

# Create .env if not exists
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - SKYFLOW_* credentials"
    echo "   - PARALLEL_AI_API_KEY"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"

# Activate and install dependencies
echo ""
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Start Redis
echo ""
echo "Starting Redis container..."
docker-compose up -d
sleep 3
echo "✓ Redis started"

# Verify Redis
echo ""
echo "Verifying Redis connection..."
if docker exec diagnosaurus-redis redis-cli ping | grep -q PONG; then
    echo "✓ Redis is healthy"
else
    echo "❌ Redis health check failed"
    exit 1
fi

# Create uploads directory
mkdir -p uploads
touch uploads/.gitkeep

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys (if not done)"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the app: python app.py"
echo "4. Visit http://localhost:5000"
echo ""
echo "🎯 Before demo: Change AGENTS_BATCH to 5 in config.py"
echo ""
