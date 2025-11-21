"""
Base agent capabilities using composition pattern
No inheritance chains - agents compose capabilities as needed
"""
import uuid
from typing import Optional, Dict, Any, List, Union
from abc import ABC, abstractmethod
from anthropic import Anthropic
from loguru import logger
from config import settings
from services.redis_service import RedisService


class ResearchCapability:
    """Mixin for web research functionality via Parallel.ai or fallback service"""

    def __init__(self, parallel_service: Any):  # Accepts ParallelService or FallbackResearchService
        self.parallel_service = parallel_service

    async def research_web(
        self,
        query: str,
        sources: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform web research on a topic"""
        logger.debug(f"Researching web: {query}")
        return await self.parallel_service.search_medical(query, sources)

    async def research_condition_details(
        self,
        condition: str,
        symptom_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Deep research on specific condition"""
        logger.debug(f"Deep research on condition: {condition}")
        return await self.parallel_service.research_condition(condition, symptom_context)


class ReasoningCapability:
    """Mixin for LLM-based reasoning functionality"""

    def __init__(self, anthropic_client: Anthropic, model: str = None):
        self.anthropic_client = anthropic_client
        self.model = model or settings.model_name

    async def reason(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = None,
    ) -> str:
        """Perform LLM reasoning without tools"""
        logger.debug(f"LLM reasoning: {prompt[:100]}...")

        try:
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=settings.max_tokens,
                temperature=temperature or settings.temperature,
                system=system_prompt or "You are a medical research assistant.",
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text
            logger.debug(f"LLM response length: {len(content)} chars")
            return content

        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}")
            return f"Error: {str(e)}"

    async def reason_with_context(
        self,
        prompt: str,
        context: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Reason with additional context (e.g., research results)"""
        # Format context for LLM
        context_str = "\n\n".join([
            f"Source: {c.get('citation', 'Unknown')}\n{c.get('content', '')}"
            for c in context
        ])

        full_prompt = f"{prompt}\n\nContext:\n{context_str}"
        return await self.reason(full_prompt, system_prompt)


class MemoryCapability:
    """Mixin for agent memory via Redis"""

    def __init__(self, redis_service: RedisService, agent_id: str):
        self.redis_service = redis_service
        self.agent_id = agent_id

    def remember(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Store information in agent memory"""
        return self.redis_service.set_agent_memory(self.agent_id, key, value, ttl)

    def recall(self, key: str) -> Optional[str]:
        """Retrieve information from agent memory"""
        return self.redis_service.get_agent_memory(self.agent_id, key)


class BaseAgent(ABC):
    """
    Base agent class - all agents inherit from this
    Agents compose capabilities via mixins
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        anthropic_client: Optional[Anthropic] = None,
        redis_service: Optional[RedisService] = None,
        parallel_service: Optional[Any] = None,  # Accepts ParallelService or FallbackResearchService
    ):
        self.agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
        self.anthropic_client = anthropic_client or Anthropic(api_key=settings.anthropic_api_key)
        self.redis_service = redis_service or RedisService()
        self.parallel_service = parallel_service

        # Compose capabilities
        self._init_capabilities()

        logger.info(f"Initialized agent: {self.agent_id} ({self.__class__.__name__})")

    def _init_capabilities(self):
        """Initialize agent capabilities - override in subclasses"""
        pass

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task - must be implemented by subclasses"""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "status": "active",
        }
