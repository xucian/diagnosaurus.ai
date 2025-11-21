# Data Persistence Strategy

## TL;DR

**Redis is the only database** - perfect for 1-user hackathon demo
- ✅ Fast (RAM-backed)
- ✅ **Persists to disk** (survives restarts)
- ✅ Simple (no migrations, no ORM)
- ✅ Good enough for demo

## What Gets Stored Where

### Redis (Memory + Disk)

| Data Type | TTL | Persisted? | Purpose |
|-----------|-----|------------|---------|
| Session data | 1 hour | ✅ Yes (RDB) | Analysis state during processing |
| Agent memory | 1 hour | ✅ Yes (RDB) | Agent context between calls |
| RedisVL vectors | No expiry | ✅ Yes (RDB/AOF) | Semantic cache for symptoms |
| Final results | 1 hour | ✅ Yes (RDB) | Completed analyses (until TTL) |

**Persistence Mechanism**:
```yaml
# docker-compose.yml
volumes:
  - redis-data:/data  # Docker volume on host disk
```

Redis uses:
- **RDB snapshots**: Periodic saves to `/data/dump.rdb`
- **AOF logs**: redis-stack enables append-only file by default

**What this means**:
- Container restart → Data intact ✅
- Server reboot → Data intact ✅
- After 1 hour TTL → Data deleted automatically ✅

### What's NOT Persisted Long-Term

❌ Expired sessions (by design)
❌ User accounts (no auth system in hackathon version)
❌ Historical analyses beyond 1 hour
❌ Audit logs

## Redis: Memory vs Disk Explained

```
┌─────────────────────────────────────┐
│  USER REQUEST                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  REDIS (RAM)                        │
│  - Fast reads/writes                │
│  - All data in memory               │
│  - 256MB limit (evicts if full)     │
└──────────────┬──────────────────────┘
               │
               │ Every N seconds or on shutdown
               ▼
┌─────────────────────────────────────┐
│  DISK (/data/dump.rdb)              │
│  - Persistent across restarts       │
│  - Background snapshots             │
│  - Loaded on container start        │
└─────────────────────────────────────┘
```

**"Long-term memory"** = Data stored in Redis (RAM) with disk backup, not expired by TTL

## Why Redis-Only is Fine for Hackathon

✅ **Fast**: <1ms reads, perfect for real-time demo
✅ **Simple**: No ORM, no migrations, just works
✅ **1-user**: No auth system needed
✅ **Demo-focused**: Data persists long enough for judging
✅ **RedisVL**: Built-in vector search for semantic caching

**If this were production**, you'd add PostgreSQL for:
- User accounts & multi-tenancy
- Permanent medical records
- Audit logs (regulatory)
- But for hackathon? Redis is perfect.

## Verify Persistence

### Check Redis is saving to disk:
```bash
# View Redis config
docker exec diagnosaurus-redis redis-cli CONFIG GET save
# Output: "900 1 300 10 60 10000" (saves every 15min if 1 change)

# Check last save time
docker exec diagnosaurus-redis redis-cli LASTSAVE

# Manually trigger save
docker exec diagnosaurus-redis redis-cli BGSAVE
```

### Test persistence:
```bash
# 1. Submit analysis → Get session_id
curl -X POST http://localhost:5000/api/analyze -d '{...}'

# 2. Restart Redis
docker-compose restart redis

# 3. Check session still exists
curl http://localhost:5000/api/status/{session_id}
# Should return data (if within 1h TTL)
```

## If Judges Ask About "Real Database"

**Answer**: "Redis IS a real database with disk persistence. For this 1-user demo, it's perfect - fast, simple, and handles sessions + semantic caching. Production would add PostgreSQL for multi-user auth and compliance, but that's overkill for the hackathon scope."

## Database Choice Justification (For Judges)

**Why Redis-only for hackathon?**

1. **Speed**: In-memory = <1ms reads
2. **Simplicity**: No ORM, no migrations
3. **Semantic Search**: RedisVL built for vector similarity
4. **Temporary Data**: Medical analyses are session-based
5. **Real-world**: Production would add PostgreSQL for compliance

**Redis-stack features used**:
- RediSearch: Vector similarity (RedisVL)
- RedisJSON: Complex data structures
- Persistence: RDB + AOF
- Pub/Sub: Real-time status updates (future enhancement)

## Data Lifecycle

```
┌─────────────────────────────────────────────┐
│ 1. User submits symptoms                    │
│    └─> Skyflow sanitizes                    │
│        └─> Stored in Redis (session_id)     │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ 2. Agents research (30s)                    │
│    └─> Agent memory in Redis (TTL: 1h)      │
│        └─> Research results cached           │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ 3. Results returned                         │
│    └─> Stored in Redis (session_id)         │
│        └─> RedisVL caches symptom vectors    │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ 4. After 1 hour TTL                         │
│    └─> Redis auto-expires session           │
│        └─> Vector cache remains (no TTL)     │
└─────────────────────────────────────────────┘
```

## Redis Backup Strategy (Production)

If deploying beyond hackathon:

```bash
# Automated backups (cron)
docker exec diagnosaurus-redis redis-cli BGSAVE
cp /var/lib/docker/volumes/diagnosaurus_redis-data/_data/dump.rdb \
   /backups/redis-$(date +%Y%m%d).rdb
```

## FAQ

**Q: Does data survive server crashes?**
A: Yes, Redis persists to disk. Last snapshot restored on restart.

**Q: What happens if Redis runs out of memory (256MB)?**
A: `allkeys-lru` policy evicts least-recently-used keys (oldest sessions first).

**Q: Can I increase session TTL?**
A: Yes, edit `config.py`:
```python
session_timeout: int = Field(default=3600, ...)  # seconds
```

**Q: Why not MongoDB?**
A: Redis is faster for cache-heavy workloads. Mongo would be overkill for session data.

**Q: What about ACID compliance?**
A: Redis supports transactions. For critical data (billing, prescriptions), you'd add PostgreSQL.

## Summary for Demo

> "We use Redis for ultra-fast session management and semantic caching with RedisVL. Data persists to disk via RDB snapshots. For production, we'd add PostgreSQL for user accounts and audit logs - schema ready in init.sql - but for hackathon velocity, Redis handles everything with <1ms latency."

---

**Bottom line**: Redis is a real database with disk persistence. "Long-term memory" = data that doesn't expire (semantic cache), but still backed by Redis snapshots.
