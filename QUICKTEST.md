# Quick Test Guide

## ✅ Fast Tests (No API Keys, <2 seconds)

```bash
# Test 1: PII Redaction
python test_pii_redaction.py

# Test 2: PDF Extraction
python test_pdf_extraction.py
```

**Both should show**: `✓ ALL TESTS PASSED`

---

## Next Steps

### If API keys ready:
```bash
# Test 3: Research Services (30-60s)
python test_research_services.py
```

### If Redis + API keys ready:
```bash
# Start Redis
docker-compose up -d

# Test 4: Full Pipeline (1-2min)
python test_full_pipeline.py
```

---

## Fixed Issues

1. ✅ **redis version** - Downgraded to 5.0.1 (compatible with redisvl)
2. ✅ **RedisVL optional** - Falls back gracefully if import fails
3. ✅ **Skyflow SDK optional** - Uses regex fallback if SDK unavailable
4. ✅ **Phone pattern** - Now catches short format (555-1234)

---

## What Works Now

✅ PII redaction (regex fallback)
✅ PDF text extraction
✅ All services load without crashes
✅ Graceful degradation (missing deps → fallback)

---

## Quick Validation

```bash
# All fast tests (no deps)
python test_pii_redaction.py && python test_pdf_extraction.py && echo "✓ Core functionality working"
```
