#!/bin/bash

set -eou pipefail

. _actvenv.sh

echo "🦖 Running Test Suite"
echo "======================"
echo ""

echo "1️⃣  PII Redaction"
python test_pii_redaction.py
echo ""

echo "2️⃣  PDF Extraction"
python test_pdf_extraction.py
echo ""

echo "3️⃣  Research Services"
python test_research_services.py
echo ""

echo "4️⃣  Full Pipeline"
python test_full_pipeline.py
echo ""

echo "✅ All tests complete"
