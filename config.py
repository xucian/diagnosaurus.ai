"""
Diagnosaurus.ai Configuration
All application settings centralized for easy tuning
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application configuration with validation"""

    # API Keys
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    skyflow_vault_id: str = Field(..., env="SKYFLOW_VAULT_ID")
    skyflow_vault_url: str = Field(..., env="SKYFLOW_VAULT_URL")
    skyflow_api_key: str = Field(..., env="SKYFLOW_API_KEY")
    parallel_ai_api_key: str = Field(..., env="PARALLEL_AI_API_KEY")

    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")

    # RedisVL Configuration
    redisvl_index_name: str = Field(default="diagnosaurus_cache", env="REDISVL_INDEX_NAME")
    redisvl_similarity_threshold: float = Field(default=0.85, env="REDISVL_SIMILARITY_THRESHOLD")

    # Flask Configuration
    flask_env: str = Field(default="development", env="FLASK_ENV")
    flask_debug: bool = Field(default=True, env="FLASK_DEBUG")
    secret_key: str = Field(..., env="SECRET_KEY")
    port: int = Field(default=5000, env="PORT")

    # MCP Server Configuration
    mcp_redis_enabled: bool = Field(default=True, env="MCP_REDIS_ENABLED")
    mcp_parallel_enabled: bool = Field(default=True, env="MCP_PARALLEL_ENABLED")

    # Agent Configuration
    # TODO: Change AGENTS_BATCH to 5 before demo for faster processing
    max_conditions: int = Field(default=5, env="MAX_CONDITIONS",
                                description="Maximum conditions to analyze")
    agents_batch: int = Field(default=2, env="AGENTS_BATCH",
                              description="Number of concurrent agents (increase to 5 for demo)")

    # Scoring Thresholds
    confidence_threshold: float = Field(default=0.50, env="CONFIDENCE_THRESHOLD",
                                       description="Minimum confidence to display condition")
    min_probability: float = Field(default=0.05, env="MIN_PROBABILITY",
                                  description="Filter conditions <5% with <50% confidence")

    # Clinic Search
    max_clinics: int = Field(default=5, env="MAX_CLINICS",
                            description="Maximum clinic results to display")
    min_clinic_rating: float = Field(default=3.5, description="Minimum Google rating")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="diagnosaurus.log", env="LOG_FILE")

    # File Paths
    base_dir: Path = Field(default=Path(__file__).parent)
    data_dir: Path = Field(default=Path(__file__).parent / "data")
    upload_dir: Path = Field(default=Path(__file__).parent / "uploads")
    geoip_db_path: Path = Field(default=Path(__file__).parent / "data" / "geoip.json")

    # Model Configuration
    model_name: str = Field(default="claude-3-5-sonnet-20241022",
                           description="Anthropic model for agents")
    max_tokens: int = Field(default=4096, description="Max tokens per agent response")
    temperature: float = Field(default=0.7, description="LLM temperature")

    # Session Configuration
    session_timeout: int = Field(default=3600, description="Session TTL in seconds (1 hour)")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=False, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=10, description="Max requests per minute")

    @validator("agents_batch")
    def validate_agents_batch(cls, v, values):
        """Ensure agents_batch doesn't exceed max_conditions"""
        max_cond = values.get("max_conditions", 5)
        if v > max_cond:
            return max_cond
        return v

    @validator("confidence_threshold", "min_probability")
    def validate_probability(cls, v):
        """Ensure probabilities are between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("Probability must be between 0 and 1")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.upload_dir.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()


# Body region coordinates for visualization (x, y positions on 800x600 SVG)
BODY_REGIONS = {
    "head": {"x": 400, "y": 80},
    "brain": {"x": 400, "y": 60},
    "eyes": {"x": 400, "y": 90},
    "ears": {"x": 450, "y": 85},
    "throat": {"x": 400, "y": 130},
    "neck": {"x": 400, "y": 150},
    "chest": {"x": 400, "y": 220},
    "heart": {"x": 380, "y": 210},
    "lungs": {"x": 420, "y": 210},
    "cardiovascular": {"x": 360, "y": 220},
    "respiratory": {"x": 440, "y": 220},
    "abdomen": {"x": 400, "y": 320},
    "stomach": {"x": 380, "y": 300},
    "liver": {"x": 430, "y": 290},
    "intestines": {"x": 400, "y": 340},
    "digestive": {"x": 400, "y": 320},
    "kidneys": {"x": 370, "y": 330},
    "urinary": {"x": 400, "y": 380},
    "reproductive": {"x": 400, "y": 400},
    "pelvis": {"x": 400, "y": 420},
    "circulatory": {"x": 340, "y": 250},
    "lymphatic": {"x": 460, "y": 250},
    "endocrine": {"x": 400, "y": 200},
    "musculoskeletal": {"x": 300, "y": 300},
    "skin": {"x": 500, "y": 300},
    "nervous": {"x": 400, "y": 100},
    "immune": {"x": 480, "y": 280},
    "blood": {"x": 340, "y": 280},
    "general": {"x": 400, "y": 350},
}


# Confidence score color mapping (for UI visualization)
CONFIDENCE_COLORS = {
    "high": "#4CAF50",      # Green: >= 0.75
    "medium": "#FFC107",    # Yellow: 0.50 - 0.74
    "low": "#FF5722",       # Red: < 0.50
}


def get_confidence_color(confidence: float) -> str:
    """Get color based on confidence score"""
    if confidence >= 0.75:
        return CONFIDENCE_COLORS["high"]
    elif confidence >= 0.50:
        return CONFIDENCE_COLORS["medium"]
    else:
        return CONFIDENCE_COLORS["low"]
