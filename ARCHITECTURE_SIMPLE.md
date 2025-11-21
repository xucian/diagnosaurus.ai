# Architecture (Simple Version)

## Database: Redis Only

**One config. One database. KISS.**

```
┌─────────────────────────────────────┐
│          Flask App (Python)         │
│  - Routes (/api/analyze, /api/status)
│  - Agent orchestration              │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│          Redis (Memory + Disk)      │
│  - Session data (1h TTL)            │
│  - Agent memory (1h TTL)            │
│  - Semantic cache (RedisVL, no TTL) │
│  - Persists to /data volume         │
└─────────────────────────────────────┘
```

## Why Redis-Only Works

✅ **1-user demo** → No need for multi-user auth
✅ **Fast** → RAM-backed, <1ms reads
✅ **Simple** → No migrations, no ORM
✅ **Persists** → Saves to disk (survives restarts)
✅ **RedisVL** → Vector search for semantic caching

## What Gets Stored

| Data | Lifespan | Why |
|------|----------|-----|
| Session state | 1 hour | Analysis in progress |
| Agent memory | 1 hour | Context between agent calls |
| Semantic cache | Forever | Speed up similar symptom searches |
| Final results | 1 hour | Return to user |

**After 1 hour**: Redis auto-deletes expired data. Clean and simple.

## Redis = Real Database

Redis is NOT just a cache. It's a real database that:
- Persists to disk (RDB snapshots)
- Survives restarts
- Supports transactions
- Has built-in vector search (RedisVL)

**"But where's PostgreSQL?"**
- Not needed for 1-user demo
- Would add for production multi-user features
- But that's scope creep for hackathon

## Docker Setup

```yaml
# docker-compose.yml (10 lines!)
services:
  redis:
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data  # Persists here
```

Done. No PostgreSQL, no SQLite, no MongoDB.

## Start Everything

```bash
docker-compose up -d  # Redis
python app.py         # Flask
```

Two commands. That's it.

## Redis Stack Includes

- **Redis Core**: Key-value store
- **RedisJSON**: Store complex objects
- **RediSearch**: Full-text search
- **RedisVL**: Vector similarity (semantic cache)
- **RedisInsight**: Web UI on port 8001

All in one image. Perfect for hackathon.

## If You Want to See Data

```bash
# CLI
docker exec -it diagnosaurus-redis redis-cli

# Or Web UI
open http://localhost:8001
```

## Memory Management

```
REDIS_ARGS=--maxmemory 256mb --maxmemory-policy allkeys-lru
```

If Redis hits 256MB:
1. Evicts least-recently-used keys
2. Oldest sessions deleted first
3. Semantic cache protected (most frequently used)

For demo, you'll never hit 256MB. One session = ~1MB.

## Summary for Judges

> "We use Redis as our primary database - it's not just a cache. With redis-stack, we get in-memory speed + disk persistence + vector search (RedisVL) for semantic caching. For a 1-user demo, this is simpler and faster than PostgreSQL. Production would add PostgreSQL for multi-tenancy, but that's out of hackathon scope."

---

**KISS**: One config (docker-compose.yml), one database (Redis), works great.
