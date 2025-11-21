#!/bin/bash
# Run all tests in sequence

set -e

echo "🦖 Diagnosaurus.ai Test Suite"
echo "======================================"
echo ""

# Check virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# Test 1: PII Redaction (fast, no dependencies)
echo "1️⃣  Testing PII Redaction (no API keys needed)"
echo "--------------------------------------"
python test_pii_redaction.py
echo ""

# Test 2: PDF Extraction (fast, no dependencies)
echo "2️⃣  Testing PDF Extraction (no API keys needed)"
echo "--------------------------------------"
python test_pdf_extraction.py
echo ""

# Test 3: Research Services (needs API keys or fallback)
echo "3️⃣  Testing Research Services (needs internet + API keys)"
echo "--------------------------------------"
python test_research_services.py
echo ""

# Test 4: Full Pipeline (slow, needs everything)
echo "4️⃣  Testing Full Pipeline (needs Redis + API keys)"
echo "--------------------------------------"
python test_full_pipeline.py
echo ""

echo "======================================"
echo "✓ ALL TEST SUITES COMPLETED"
echo "======================================"
