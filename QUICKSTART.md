# 🚀 Diagnosaurus.ai - Quickstart Guide

## 30-Second Setup

```bash
# 1. Setup (first time only)
./setup.sh

# 2. Add your API keys to .env
# Edit ANTHROPIC_API_KEY, SKYFLOW_*, PARALLEL_AI_API_KEY

# 3. Run
./run.sh

# 4. Test
# Visit http://localhost:5000
```

## Test Symptoms (Copy/Paste Ready)

```
Persistent fatigue for 2 weeks, dizziness when standing, pale skin,
shortness of breath during light exercise, cold hands and feet,
rapid heartbeat, difficulty concentrating
```

Expected result: Iron Deficiency Anemia (high probability)

## Project Structure

```
diagnosaurus.ai/
├── CLAUDE.md                  # Comprehensive dev guide (READ THIS!)
├── HACKATHON_CHECKLIST.md     # Demo day checklist
├── README.md                  # Project overview
├── app.py                     # Flask application (main entry)
├── config.py                  # All configuration settings
├── agents/                    # Multi-agent system
│   ├── base_agent.py          # Capability mixins (composition pattern)
│   ├── research_agent.py      # Coarse + Deep research agents
│   ├── forum_coordinator.py   # Adversarial debate logic
│   └── condition_analyzer.py  # Scoring + filtering
├── services/                  # External integrations
│   ├── redis_service.py       # Memory + semantic caching
│   ├── skyflow_service.py     # Data sanitization
│   ├── parallel_service.py    # Medical research + clinics
│   └── geoip_service.py       # Location lookup
├── models/                    # Pydantic schemas
│   └── schemas.py             # Type-safe data models
├── templates/                 # Frontend HTML
│   └── index.html
└── static/                    # CSS + JavaScript
    ├── css/style.css
    └── js/app.js
```

## Key Files to Understand

### 1. `CLAUDE.md` - Your Senior Dev Guide
Complete architecture, patterns, and implementation details.

### 2. `app.py` - Main Orchestration
```python
# Key function: run_analysis_pipeline()
# This orchestrates all agents and services
```

### 3. `agents/research_agent.py` - Core Agent Logic
```python
# CoarseSearchAgent: Identifies potential conditions
# DeepResearchAgent: Investigates each condition
```

### 4. `agents/forum_coordinator.py` - Adversarial Debate
```python
# AdversarialForum: Cross-validates agent findings
```

### 5. `config.py` - All Settings
```python
# IMPORTANT: Change agents_batch from 2 to 5 before demo!
agents_batch: int = Field(default=2, ...)  # TODO: 5 for demo
```

## Common Tasks

### View Logs
```bash
tail -f diagnosaurus.log
```

### Check Redis
```bash
docker exec -it diagnosaurus-redis redis-cli ping
# Should return: PONG
```

### View Redis Data (UI)
```bash
# Open http://localhost:8001 (RedisInsight)
```

### Clear Cache
```bash
docker exec -it diagnosaurus-redis redis-cli FLUSHDB
```

### Restart Everything
```bash
docker-compose restart
```

## API Usage (Alternative to UI)

### Submit Analysis
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "Persistent fatigue, dizziness, pale skin",
    "patient_age": 35,
    "patient_sex": "female"
  }'

# Returns: {"session_id": "session_abc123", ...}
```

### Check Status
```bash
curl http://localhost:5000/api/status/session_abc123
```

## Sponsor Tools Integration

### 1. Anthropic MCP SDK
**Where**: `agents/base_agent.py`
```python
from anthropic import Anthropic
# Used for all agent reasoning
```

### 2. Redis MCP Server
**Where**: `services/redis_service.py`
```python
from redisvl.index import SearchIndex
# Semantic caching for symptoms
```

### 3. Parallel.ai MCP
**Where**: `services/parallel_service.py`
```python
# Medical research + clinic discovery
await parallel_service.search_medical(...)
await parallel_service.find_clinics(...)
```

### 4. Skyflow
**Where**: `services/skyflow_service.py`
```python
from skyflow.vault import Client
# Data sanitization/tokenization
```

## Demo Optimization

### Before Demo Day

1. **Increase Agent Batch Size** (in `config.py`):
```python
agents_batch: int = Field(default=5, ...)  # Change from 2
```

2. **Test Full Pipeline**:
```bash
./run.sh
# Submit test symptoms
# Verify results in <30 seconds
```

3. **Clear Cache**:
```bash
docker exec -it diagnosaurus-redis redis-cli FLUSHDB
```

4. **Check All Services**:
```bash
python test_setup.py
```

## Troubleshooting

### Error: "Redis connection failed"
```bash
docker-compose up -d
docker-compose logs redis
```

### Error: "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Anthropic API key invalid"
```bash
# Check .env file
cat .env | grep ANTHROPIC_API_KEY
```

### Slow Performance
- Increase `AGENTS_BATCH` in config.py
- Check Redis cache hit rate in logs
- Reduce `MAX_CONDITIONS` for testing

## Performance Metrics

Target metrics with optimized settings:
- Analysis time: <30 seconds
- Agent batch size: 5 concurrent
- Cache hit rate: >60% (after warmup)
- Conditions analyzed: 5 max
- Clinics returned: 5 max

## Next Steps

1. ✅ Run `./setup.sh`
2. ✅ Edit `.env` with API keys
3. ✅ Run `./run.sh`
4. ✅ Test with sample symptoms
5. ✅ Read `CLAUDE.md` for architecture details
6. ✅ Read `HACKATHON_CHECKLIST.md` for demo prep

## Support

- **Redis issues**: Check `docker-compose logs redis`
- **Flask errors**: Check `diagnosaurus.log`
- **API errors**: Check `.env` file
- **MCP issues**: Check `~/.mcp/logs/`

---

**Good luck at the hackathon! 🦖🚀**
