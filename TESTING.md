# Testing Guide

## Quick Start

```bash
# Run all tests
./run_tests.sh

# Or run individually
python test_pii_redaction.py      # Fast, no deps
python test_pdf_extraction.py     # Fast, no deps
python test_research_services.py  # Needs API keys
python test_full_pipeline.py      # Needs Redis + API keys
```

---

## Test Files

### 1. `test_pii_redaction.py`
**Tests**: PII/PHI redaction (SSN, email, phone, DOB, MRN)

**Requirements**: None (uses regex fallback)

**Duration**: <1 second

**What it tests**:
- Individual PII patterns (SSN, email, phone, etc.)
- Combined text (symptoms + documents)
- No false positives (normal text unchanged)

**Run**:
```bash
python test_pii_redaction.py
```

**Expected output**:
```
✓ PASS - SSN
✓ PASS - Email
✓ PASS - Phone
...
✓ ALL TESTS PASSED
```

---

### 2. `test_pdf_extraction.py`
**Tests**: PDF text extraction

**Requirements**: pypdf (in requirements.txt)

**Duration**: <1 second

**What it tests**:
- Basic PDF parsing
- Multiple documents
- Invalid PDF handling
- Real-world simulation (symptoms + docs)

**Run**:
```bash
python test_pdf_extraction.py
```

**Expected output**:
```
✓ PASS - Extracted 50 characters
✓ PASS - Combined 120 chars from 2 docs
...
✓ ALL TESTS PASSED
```

---

### 3. `test_research_services.py`
**Tests**: Medical research + clinic discovery

**Requirements**:
- API keys: `ANTHROPIC_API_KEY`, `PARALLEL_AI_API_KEY` (or fallback)
- Internet connection

**Duration**: 30-60 seconds

**What it tests**:
- Service selection (Parallel.ai vs fallback)
- Medical search
- Clinic discovery
- Condition deep research

**Run**:
```bash
# With Parallel.ai
python test_research_services.py

# With fallback (DuckDuckGo + Chrome)
# Set in .env: USE_FALLBACK_RESEARCH=true
python test_research_services.py
```

**Expected output**:
```
Using: ParallelService (or FallbackResearchService)
✓ PASS - Medical search (Found 3 results)
✓ PASS - Clinic search (Found 5 clinics)
...
✓ ALL TESTS PASSED
```

---

### 4. `test_full_pipeline.py`
**Tests**: Complete end-to-end analysis

**Requirements**:
- Redis running: `docker-compose up -d`
- API keys: `ANTHROPIC_API_KEY`, `PARALLEL_AI_API_KEY`
- Internet connection

**Duration**: 1-2 minutes

**What it tests**:
- Redis integration
- Document processing
- Full agent pipeline:
  1. PII sanitization
  2. Coarse search
  3. Deep research (2 conditions)
  4. Adversarial forum
  5. Final scoring

**Run**:
```bash
# Start Redis first
docker-compose up -d

# Run test
python test_full_pipeline.py
```

**Expected output**:
```
[1/5] Sanitizing text...
  ✓ Sanitized 150 → 148 chars
[2/5] Coarse search...
  ✓ Identified 5 conditions
...
RESULTS
1. Iron Deficiency Anemia
   Probability: 72%
   Confidence:  85%
...
✓ PASS - Pipeline completed
```

---

## Test Scenarios

### Scenario 1: Quick Validation (No API Keys)
**Tests regex + PDF only**

```bash
python test_pii_redaction.py
python test_pdf_extraction.py
```

**Use case**: Verify core functionality before adding API keys

---

### Scenario 2: Research Services Check
**Tests API integration**

```bash
# With Parallel.ai
python test_research_services.py

# With fallback (no Parallel.ai key)
USE_FALLBACK_RESEARCH=true python test_research_services.py
```

**Use case**: Verify external API connections

---

### Scenario 3: Full System Test
**Tests everything**

```bash
docker-compose up -d
./run_tests.sh
```

**Use case**: Pre-demo validation

---

## Troubleshooting

### Test fails: "Redis connection failed"
```bash
# Start Redis
docker-compose up -d

# Verify
docker ps | grep redis
```

### Test fails: "Anthropic API key not found"
```bash
# Check .env
cat .env | grep ANTHROPIC_API_KEY

# Should see: ANTHROPIC_API_KEY=sk-ant-...
```

### Test slow: Research taking >60s
```bash
# Switch to fallback mode
echo "USE_FALLBACK_RESEARCH=true" >> .env

# Or reduce test scope in test_full_pipeline.py
# Edit line: conditions[:2]  # Only test 2 conditions
```

### PDF extraction returns empty
**Expected for minimal PDFs**. Real PDFs will have content. Mock PDF in test is minimal for speed.

---

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    docker-compose up -d
    source venv/bin/activate
    python test_pii_redaction.py
    python test_pdf_extraction.py
```

### Quick Health Check (Pre-commit)
```bash
python test_pii_redaction.py && echo "✓ Ready to commit"
```

---

## Test Output Explained

### ✓ PASS
Test succeeded, functionality works as expected

### ✗ FAIL
Test failed, check error message

### ⚠️ WARNING
Test skipped (e.g., missing Redis), not critical

---

## Performance Benchmarks

| Test | Duration | API Calls |
|------|----------|-----------|
| PII Redaction | <1s | 0 |
| PDF Extraction | <1s | 0 |
| Research Services | 30-60s | 3-5 |
| Full Pipeline | 1-2min | 10-15 |

---

## What's NOT Tested

**Intentionally omitted for hackathon scope**:
- UI/frontend (manual test via browser)
- Load testing (single-user app)
- Security penetration (out of scope)
- LLM output quality (subjective)

**Focus**: Core functionality, integrations, error handling

---

## Pre-Demo Checklist

```bash
# 1. Start services
docker-compose up -d

# 2. Quick validation
python test_pii_redaction.py

# 3. Full test (if time permits)
./run_tests.sh

# 4. Manual UI test
python app.py
# Visit http://localhost:5000
# Submit: "Fatigue, pale skin, call 555-1234"
```

---

## Summary

**Fast tests** (no deps): PII + PDF
**Integration tests** (API keys): Research services
**E2E test** (everything): Full pipeline

**Total runtime**: ~3 minutes for all tests

**Recommended**: Run PII + PDF before every commit. Run full suite before demo.
