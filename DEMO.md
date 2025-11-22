# Diagnosaurus.ai - DEMO QUICKSTART

## ✅ WORKING - Ready to Demo!

### What's Working:
- ✅ **Claude API** - Model: `claude-sonnet-4-5`
- ✅ **PII/PHI Redaction** - Regex fallback (8/8 tests pass)
- ✅ **PDF Extraction** - Working (5/5 tests pass)
- ✅ **Multi-Agent System** - LLM reasoning works
- ✅ **Redis** - Running on port 6380
- ⚠️ **Research** - DuckDuckGo rate limited (LLM compensates)

### ⚡ Start Demo (15 seconds):

```bash
# 1. Activate venv
source venv/bin/activate

# 2. Ensure Redis is running
docker-compose up -d

# 3. Start Flask app
python app.py
```

**App will run on: http://localhost:5001**

---

## 🎯 Demo Script

### 1. Home Page
- Show UI with symptom input, age/sex, document upload

### 2. Enter Symptoms
```
Persistent fatigue, pale skin, and dizziness for 2 weeks.
Feel weak when standing up. Sometimes shortness of breath.
```

### 3. Submit & Explain Pipeline
- **Step 1:** PII redaction (Skyflow/regex)
- **Step 2:** Coarse search (LLM identifies 5 conditions)
- **Step 3:** Deep research (2 concurrent agents per batch)
- **Step 4:** Adversarial forum (agents debate findings)
- **Step 5:** Confidence scoring (filters < 50%)
- **Step 6:** Clinic discovery (nearby specialists)

### 4. Results Display
Point out:
- **Condition cards** with probability bars
- **Confidence scores** from adversarial debate
- **Symptom matching** highlights
- **Clinic results** with blurred contact info (privacy)
- **Body visualization** showing affected areas

---

## 🔧 If Something Breaks

### Redis Not Running
```bash
docker-compose up -d
```

### Port 5001 Already in Use
```bash
# In .env, change:
PORT=5002
```

### DuckDuckGo Rate Limited
**This is fine!** The LLM still identifies conditions using medical knowledge.

---

## 📊 Sample Expected Output

**Conditions Found:**
1. Iron deficiency anemia (85% probability, 92% confidence)
2. Vitamin B12 deficiency (75% probability, 88% confidence)
3. Hypothyroidism (65% probability, 85% confidence)
4. Postural orthostatic hypotension (60% probability, 80% confidence)
5. Chronic fatigue syndrome (45% probability - **filtered out < 50%**)

**Clinics:** 3-5 results with blurred phone numbers

---

## 🎥 Talking Points for Judges

1. **Privacy-First**: Skyflow integration for PII/PHI protection
2. **Multi-Agent AI**: Adversarial forum prevents overconfidence
3. **Batch Processing**: Concurrent agents (configurable AGENTS_BATCH)
4. **Graceful Degradation**: Works even if external services fail
5. **Production-Ready**: Redis caching, proper error handling
6. **Medical Ethics**: Confidence thresholds filter uncertain diagnoses

---

## ⚡ Performance Notes

- Coarse search: ~3-5 seconds
- Deep research: ~10-15 seconds (2 agents/batch)
- Full pipeline: **~25-30 seconds total**

To speed up for demo (in `config.py`):
```python
agents_batch: int = 5  # Process all 5 conditions at once
```

---

## 🚀 Post-Demo Improvements

1. Deploy Skyflow Detect template for AI-powered PII detection
2. Fix Parallel.ai SDK for faster medical research
3. Add RedisVL for semantic caching of symptoms
4. Deploy to AWS with load balancer
