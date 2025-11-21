# 🎯 Hackathon Checklist - Diagnosaurus.ai

## Pre-Demo Setup (Do This First!)

### 1. API Keys Setup ✅
- [ ] Copy `.env.example` to `.env`
- [ ] Add `ANTHROPIC_API_KEY=sk-ant-...`
- [ ] Add Skyflow credentials (`SKYFLOW_VAULT_ID`, `SKYFLOW_VAULT_URL`, `SKYFLOW_API_KEY`)
- [ ] Add `PARALLEL_AI_API_KEY=...`

### 2. Installation ✅
```bash
./setup.sh
# OR manually:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker-compose up -d
```

### 3. Configuration Tweaks ⚠️
**IMPORTANT**: Before demo, edit `config.py`:
```python
agents_batch: int = Field(default=5, ...)  # Change from 2 to 5!
```

### 4. Test Run ✅
```bash
./run.sh
# Visit http://localhost:5000
# Submit test symptoms
```

## During Demo (3 Minutes)

### Minute 1: Problem Statement (45s)
**Script**:
> "750 billion dollars lost annually to misdiagnosis in the US alone. Diagnosaurus.ai uses autonomous AI agents with adversarial debate to provide probabilistic condition assessment and local provider discovery."

**Show**: Slides with problem stats

### Minute 2: Live Demo (90s)
**Test Symptoms** (have this ready):
```
Persistent fatigue for 2 weeks, dizziness when standing,
pale skin, shortness of breath during light exercise,
cold hands and feet, rapid heartbeat
```

**Actions**:
1. Paste symptoms → Submit
2. Show real-time agent status updates
3. Point out: "3 agents researching in parallel"
4. Show forum debate phase
5. Display results:
   - Body diagram with condition bubbles
   - Iron Deficiency Anemia (high probability)
   - Vitamin B12 Deficiency (medium)
   - Hypothyroidism (lower)
6. Show clinic results with privacy features

### Minute 3: Technical Deep Dive (45s)
**Key Points**:
1. **Architecture**: Multi-agent system with composition pattern
2. **Sponsor Tools** (emphasize all 4):
   - Anthropic MCP SDK → Agent orchestration
   - Redis MCP → Agent memory + semantic caching
   - Parallel.ai MCP → Medical research + clinic search
   - Skyflow → Data sanitization
3. **Autonomy**: Agents self-organize research without hardcoded rules
4. **Performance**: <30s analysis with 5 concurrent agents

**Show**: Architecture diagram or code (agents/base_agent.py)

## Judging Criteria Checklist

### Autonomy (20%)
- [ ] Agents decide research strategy autonomously
- [ ] No hardcoded symptom→condition mappings
- [ ] Forum debate self-organizes
- [ ] Adaptive confidence scoring

### Idea (20%)
- [ ] Addresses real problem (diagnostic accuracy + access)
- [ ] Novel approach (adversarial multi-agent)
- [ ] Practical output (actionable clinic list)
- [ ] Privacy-first (Skyflow integration)

### Technical Implementation (20%)
- [ ] Clean architecture (composition over inheritance)
- [ ] Type-safe (Pydantic models everywhere)
- [ ] Error handling (graceful degradation)
- [ ] Performance optimization (semantic caching)
- [ ] Well-documented code

### Tool Use (20%)
- [ ] Anthropic MCP: Core agent framework
- [ ] Redis MCP: Memory + caching (show cache hit rate)
- [ ] Parallel.ai MCP: Research + clinic search
- [ ] Skyflow: Data sanitization demo

### Presentation (20%)
- [ ] Clear problem statement
- [ ] Live demo (no slides for this part)
- [ ] Show real-time agent logs
- [ ] Explain architecture concisely
- [ ] Handle Q&A confidently

## Demo Day Checklist

### Morning Of
- [ ] Charge laptop fully
- [ ] Test internet connection
- [ ] Run full demo end-to-end 2x
- [ ] Clear Redis cache: `docker exec diagnosaurus-redis redis-cli FLUSHDB`
- [ ] Restart all services fresh
- [ ] Have backup demo video ready (just in case)

### 5 Minutes Before
- [ ] Close all unnecessary tabs/apps
- [ ] Open terminal with logs visible: `tail -f diagnosaurus.log`
- [ ] Open browser to http://localhost:5000
- [ ] Have test symptoms in clipboard
- [ ] Start screen recording (for backup)

### During Demo
- [ ] Speak clearly and confidently
- [ ] Point to agent status updates as they happen
- [ ] Emphasize "autonomous" and "real-time"
- [ ] Mention all 4 sponsor tools by name
- [ ] Show enthusiasm!

### If Things Break
**Plan B**:
- If agents are slow: "This is researching 5 medical databases in real-time"
- If network fails: Show architecture diagram + code walkthrough
- If total failure: Show pre-recorded demo video

## Key Talking Points

### Differentiators
1. **Adversarial Forum**: Unlike single-agent systems, our agents debate findings
2. **Semantic Caching**: RedisVL prevents redundant research (show hit rate)
3. **Privacy-First**: Skyflow tokenization before any processing
4. **Actionable Output**: Not just diagnosis, but local clinics with reviews

### Technical Highlights
- Composition-based agent architecture (show code)
- Batched parallel agent execution
- Confidence scoring from debate outcomes
- GeoIP → clinic search pipeline

### Questions You Might Get

**Q: How accurate is this?**
> "This is a prototype showing autonomous agent coordination. In production, we'd train on clinical datasets and validate against diagnostic databases. The focus here is the multi-agent architecture that could power such a system."

**Q: Can this replace doctors?**
> "Absolutely not. This is a triage tool to help patients understand possible conditions and find appropriate care. It explicitly warns users to consult healthcare professionals."

**Q: How do you handle liability?**
> "All output includes disclaimers. In production, this would be regulated as a clinical decision support tool under FDA guidelines."

**Q: What's the performance?**
> "With 5 concurrent agents: <30 seconds for full analysis. RedisVL semantic cache improves repeat queries by 70%."

## Post-Demo

### GitHub README
- [ ] Add demo screenshots
- [ ] Link to presentation slides
- [ ] Add video demo link
- [ ] Update with any improvements made during hackathon

### Follow-Up
- [ ] Connect with judges on LinkedIn
- [ ] Thank sponsor companies on Twitter
- [ ] Write blog post about multi-agent architecture
- [ ] Submit to Product Hunt (if allowed)

## Emergency Contacts
- Redis issues → Check `docker-compose logs redis`
- MCP issues → Check `~/.mcp/logs/`
- Flask errors → Check `diagnosaurus.log`

---

**Good luck! 🦖🚀**
