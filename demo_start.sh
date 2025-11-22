#!/bin/bash
# Diagnosaurus.ai - Demo Startup Script
set -e

echo "============================================================"
echo "DIAGNOSAURUS.AI - STARTING DEMO"
echo "============================================================"

# 1. Check venv
if [ ! -d "venv" ]; then
    echo "❌ No venv found. Run: python3 -m venv venv"
    exit 1
fi

echo "✓ Activating venv..."
source venv/bin/activate

# 2. Start Redis
echo "✓ Starting Redis..."
docker-compose up -d 2>/dev/null || echo "⚠️  Redis may already be running"

# 3. Check API keys
if [ ! -f ".env" ]; then
    echo "❌ No .env file found!"
    exit 1
fi

echo "✓ Checking API keys..."
python3 << 'EOF'
from config import settings
import sys

missing = []
if not settings.anthropic_api_key or settings.anthropic_api_key == "":
    missing.append("ANTHROPIC_API_KEY")

if missing:
    print(f"❌ Missing: {', '.join(missing)}")
    sys.exit(1)

print(f"✓ API keys configured")
print(f"✓ Model: {settings.model_name}")
print(f"✓ Port: {settings.port}")
EOF

if [ $? -ne 0 ]; then
    echo "Fix .env and try again"
    exit 1
fi

# 4. Start Flask
echo ""
echo "============================================================"
echo "🚀 STARTING FLASK APP"
echo "============================================================"
python app.py
