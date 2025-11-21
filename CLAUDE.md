# Diagnosaurus.ai - AI-Powered Medical Symptom Analysis

## Overview

Multi-agent AI system for medical symptom analysis that provides probabilistic condition assessments with local clinic recommendations.

## Architecture

### System Flow
1. User submits symptoms + optional medical documents
2. Skyflow sanitizes sensitive medical data
3. Multi-agent research phase:
   - Coarse search agent identifies potential conditions
   - Deep research agents investigate each condition in parallel
4. Adversarial forum: agents debate findings
5. Generate confidence scores and probabilities
6. Find local clinics via GeoIP + Parallel.ai
7. Visualize results on interactive body diagram

### Tech Stack
- **Backend**: Flask
- **AI**: Anthropic MCP SDK + Claude
- **Memory**: Redis MCP Server + RedisVL semantic caching
- **Security**: Skyflow for PII/PHI sanitization
- **Research**: Parallel.ai MCP
- **Frontend**: Vanilla JS

## Design Principles

- **Composition over inheritance**: Agent capabilities as mixins
- **Service layer abstraction**: External integrations isolated in `services/`
- **Configuration-driven**: Settings in `config.py`

## Agent System

### Phase 1: Coarse Search
Identifies high-level medical domains using LLM reasoning + Parallel.ai research

### Phase 2: Deep Research
Parallel agents investigate each condition via LLM intuition + medical database queries

### Phase 3: Adversarial Forum
Agents cross-validate findings through structured debate to generate final confidence scores

## Memory Architecture

- **Short-term (Redis)**: Session state, agent context
- **Long-term (RedisVL)**: Semantic cache of symptom→condition mappings for performance
- **Persistence**: Docker volume with RDB snapshots

## Security

Skyflow handles tokenization of medical documents and PII throughout the pipeline

## Key Integrations

- **Anthropic MCP**: Agent orchestration
- **Redis MCP**: Memory + caching
- **Parallel.ai MCP**: Medical research + clinic discovery
- **Skyflow**: Data sanitization

## Project Structure

- `agents/`: Agent implementations (base, research, forum coordinator)
- `services/`: External integrations (Skyflow, Parallel.ai, Redis, GeoIP)
- `models/`: Pydantic schemas
- `static/` & `templates/`: Frontend assets
