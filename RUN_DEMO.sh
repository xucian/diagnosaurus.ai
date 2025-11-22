#!/bin/bash
# ONE-COMMAND DEMO START

clear
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         DIAGNOSAURUS.AI - HACKATHON DEMO                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Kill any existing Flask processes
pkill -f "python app.py" 2>/dev/null || true

# Activate venv
source venv/bin/activate

# Start Redis quietly
docker-compose up -d 2>&1 | grep -v "Container.*Running" || true

# Quick check
python3 << 'PYEOF'
from config import settings
print(f"✓ Model: {settings.model_name}")
print(f"✓ Port: {settings.port}")
print("")
PYEOF

echo "🚀 Starting Flask..."
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Open browser: http://localhost:5000                      ║"
echo "║  Press Ctrl+C to stop                                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Run Flask (suppress most logs)
export FLASK_ENV=production
python app.py 2>&1 | grep -E "(Running on|WARNING|ERROR|Starting|Listening)" || python app.py
