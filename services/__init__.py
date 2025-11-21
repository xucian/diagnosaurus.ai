"""External service integrations"""
from .redis_service import RedisService
from .skyflow_service import SkyflowService
from .parallel_service import ParallelService, get_research_service
from .geoip_service import GeoIPService
from .document_service import DocumentService
from .duckduckgo_service import DuckDuckGoService
from .lightpanda_service import LightpandaService
from .chrome_service import ChromeService
from .fallback_research_service import FallbackResearchService

__all__ = [
    "RedisService",
    "SkyflowService",
    "ParallelService",
    "GeoIPService",
    "DocumentService",
    "DuckDuckGoService",
    "LightpandaService",
    "ChromeService",
    "FallbackResearchService",
    "get_research_service",  # Factory function to switch between Parallel.ai and fallback
]
