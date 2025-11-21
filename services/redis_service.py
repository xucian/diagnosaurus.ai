"""
Redis service for agent memory and semantic caching
Integrates with Redis MCP Server + RedisVL
"""
import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import timedelta
import redis
from loguru import logger
from config import settings

# Optional RedisVL for semantic caching
try:
    from redisvl.index import SearchIndex
    from redisvl.query import VectorQuery
    from redisvl.query.filter import Tag
    REDISVL_AVAILABLE = True
except ImportError:
    REDISVL_AVAILABLE = False
    logger.warning("RedisVL not available - semantic caching disabled")


class RedisService:
    """Redis-based memory and caching service"""

    def __init__(self):
        """Initialize Redis connection and RedisVL index"""
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=True,
        )
        self._init_semantic_cache()
        logger.info("Redis service initialized")

    def _init_semantic_cache(self):
        """Initialize RedisVL semantic cache index"""
        if not REDISVL_AVAILABLE:
            logger.info("RedisVL not available, semantic caching disabled")
            self.search_index = None
            return

        try:
            # Create index schema for symptom embeddings
            schema = {
                "index": {
                    "name": settings.redisvl_index_name,
                    "prefix": "symptom:",
                },
                "fields": [
                    {"name": "symptom_text", "type": "text"},
                    {"name": "embedding", "type": "vector", "attrs": {
                        "dims": 1536,  # Claude embeddings dimension
                        "distance_metric": "cosine",
                        "algorithm": "flat",
                    }},
                    {"name": "conditions", "type": "text"},
                    {"name": "timestamp", "type": "numeric"},
                ],
            }
            self.search_index = SearchIndex.from_dict(schema)
            self.search_index.create(overwrite=False)
            logger.info("RedisVL semantic cache initialized")
        except Exception as e:
            logger.warning(f"Semantic cache init failed (may already exist): {e}")
            self.search_index = None

    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from Redis"""
        try:
            data = self.client.get(f"session:{session_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def set_session_data(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Store session data in Redis with optional TTL"""
        try:
            ttl = ttl or settings.session_timeout
            self.client.setex(
                f"session:{session_id}",
                ttl,
                json.dumps(data)
            )
            logger.debug(f"Stored session {session_id} with TTL {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Failed to set session {session_id}: {e}")
            return False

    def get_agent_memory(self, agent_id: str, key: str) -> Optional[str]:
        """Retrieve agent-specific memory"""
        try:
            return self.client.hget(f"agent:{agent_id}:memory", key)
        except Exception as e:
            logger.error(f"Failed to get agent memory: {e}")
            return None

    def set_agent_memory(self, agent_id: str, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Store agent-specific memory"""
        try:
            self.client.hset(f"agent:{agent_id}:memory", key, value)
            if ttl:
                self.client.expire(f"agent:{agent_id}:memory", ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set agent memory: {e}")
            return False

    def cache_symptom_analysis(
        self,
        symptom_text: str,
        conditions: List[Dict[str, Any]],
        embedding: Optional[List[float]] = None
    ) -> bool:
        """Cache symptom analysis results with semantic embedding"""
        try:
            if not self.search_index or not embedding:
                # Fallback to simple key-value cache
                cache_key = self._generate_cache_key(symptom_text)
                return self.client.setex(
                    f"cache:{cache_key}",
                    3600,  # 1 hour TTL
                    json.dumps(conditions)
                )

            # Use semantic cache with vector similarity
            doc = {
                "symptom_text": symptom_text,
                "embedding": embedding,
                "conditions": json.dumps(conditions),
                "timestamp": int(time.time()),
            }
            cache_key = f"symptom:{self._generate_cache_key(symptom_text)}"
            self.search_index.load([doc], keys=[cache_key])
            logger.info(f"Cached symptom analysis with semantic embedding")
            return True
        except Exception as e:
            logger.error(f"Failed to cache symptom analysis: {e}")
            return False

    def search_similar_symptoms(
        self,
        symptom_text: str,
        embedding: List[float],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for similar cached symptoms using vector similarity"""
        try:
            if not self.search_index:
                return []

            query = VectorQuery(
                vector=embedding,
                vector_field_name="embedding",
                return_fields=["symptom_text", "conditions", "timestamp"],
                num_results=top_k,
            )
            results = self.search_index.query(query)

            similar = []
            for result in results:
                similarity_score = 1 - float(result.get("vector_distance", 1.0))
                if similarity_score >= settings.redisvl_similarity_threshold:
                    similar.append({
                        "symptom_text": result.get("symptom_text"),
                        "conditions": json.loads(result.get("conditions", "[]")),
                        "similarity": similarity_score,
                    })
            logger.info(f"Found {len(similar)} similar cached symptoms")
            return similar
        except Exception as e:
            logger.error(f"Failed to search similar symptoms: {e}")
            return []

    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.sha256(text.lower().strip().encode()).hexdigest()[:16]

    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


import time
