# 🦖 Diagnosaurus.ai

**AI-Powered Multi-Agent Medical Symptom Analysis System**

Built for hackathon: Autonomous agents + Real-time research + Local clinic discovery

## 🎯 Project Overview

Diagnosaurus.ai uses a crew of AI agents to analyze medical symptoms through:

1. **Data Ingestion** → User symptoms + medical documents
2. **Data Sanitization** → Skyflow tokenization
3. **Agent Research** → Multi-agent parallel investigation
4. **Adversarial Forum** → Cross-validation debate
5. **Condition Scoring** → Probabilistic assessment
6. **Clinic Discovery** → Local provider recommendations

## 🏗️ Architecture

- **Backend**: Flask (Python 3.11+)
- **Database**: Redis only (fast, simple, persists to disk)
- **AI**: Anthropic Claude via MCP SDK
- **Memory**: Redis MCP Server + RedisVL semantic caching
- **Security**: Skyflow API for data sanitization
- **Research**: Parallel.ai MCP for medical search
- **Frontend**: Vanilla JS (hackathon-optimized)

*Note: Redis-only is perfect for 1-user demo. No PostgreSQL/SQLite needed.*

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose
- API Keys:
  - Anthropic API key
  - Skyflow credentials
  - Parallel.ai API key

### 2. Setup

```bash
# Clone and enter directory
cd diagnosaurus.ai

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Redis
docker-compose up -d

# Verify Redis is running
docker ps | grep diagnosaurus-redis
```

### 3. Run

```bash
# Development mode
python app.py

# Visit http://localhost:5000
```

### 4. Test

```bash
# Submit symptoms via UI or API:
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "Persistent fatigue, dizziness, pale skin, shortness of breath",
    "patient_age": 35,
    "patient_sex": "female"
  }'

# Poll for results:
curl http://localhost:5000/api/status/{session_id}
```

## ⚙️ Configuration

Edit `config.py` or set environment variables:

**Critical Settings**:
- `MAX_CONDITIONS = 5`: Maximum conditions to analyze
- `AGENTS_BATCH = 2`: Concurrent agents (⚠️ TODO: change to 5 before demo)
- `CONFIDENCE_THRESHOLD = 0.50`: Minimum confidence filter
- `MIN_PROBABILITY = 0.05`: Filter low-prob conditions

## 📊 Judging Criteria Alignment

| Criterion | Score | Implementation |
|-----------|-------|----------------|
| **Autonomy** | 20% | Agents self-organize research without hardcoded rules |
| **Idea** | 20% | Addresses real problem (diagnostic accuracy + access) |
| **Technical** | 20% | Multi-agent debate + semantic caching architecture |
| **Tool Use** | 20% | 4 sponsor tools deeply integrated |
| **Presentation** | 20% | Live demo with real-time agent logs |

## 🛠️ Sponsor Tools

1. **Anthropic MCP SDK** - Agent orchestration
2. **Redis MCP Server** - Agent memory + semantic cache
3. **Parallel.ai MCP** - Medical research + clinic search
4. **Skyflow** - Data sanitization (bonus)

## 📁 Project Structure

```
diagnosaurus.ai/
├── CLAUDE.md              # Comprehensive dev guide
├── app.py                 # Main Flask application
├── config.py              # Configuration
├── agents/                # Multi-agent system
│   ├── base_agent.py      # Capability mixins
│   ├── research_agent.py  # Coarse + Deep research
│   ├── forum_coordinator.py  # Adversarial debate
│   └── condition_analyzer.py # Scoring + filtering
├── services/              # External integrations
│   ├── redis_service.py
│   ├── skyflow_service.py
│   ├── parallel_service.py
│   └── geoip_service.py
├── models/                # Pydantic schemas
├── templates/             # Frontend HTML
└── static/                # CSS + JS
```

## 🎬 Demo Script (3 minutes)

**Minute 1** - Problem & Solution
- Show misdiagnosis statistics
- Explain multi-agent approach

**Minute 2** - Live Demo
- Submit symptoms
- Show agent logs in real-time
- Display results visualization

**Minute 3** - Technical Deep Dive
- Agent debate architecture
- Sponsor tool integrations
- Performance metrics

## 🧪 Development Tips

**View Redis data**:
```bash
docker-compose --profile debug up
# Visit http://localhost:8081 for Redis Commander
```

**Check logs**:
```bash
tail -f diagnosaurus.log
```

**Reset session**:
```bash
# Connect to Redis
docker exec -it diagnosaurus-redis redis-cli
# Clear all sessions
FLUSHDB
```

## 🐛 Troubleshooting

**Redis connection failed**:
```bash
docker-compose restart redis
docker-compose logs redis
```

**MCP server not responding**:
```bash
# Check MCP server status
mcp list
# Restart if needed
mcp restart redis-mcp
```

**Slow agent execution**:
- Increase `AGENTS_BATCH` in config.py
- Check Redis cache hit rate in logs
- Reduce `MAX_CONDITIONS` for faster testing

## 📝 License

MIT License - Built for [Hackathon Name]

## 🙏 Credits

- Anthropic Claude & MCP SDK
- Redis & RedisVL
- Skyflow
- Parallel.ai

---

**⚠️ Important**: This is a prototype for educational/hackathon purposes. NOT for real medical diagnosis. Always consult qualified healthcare professionals.
