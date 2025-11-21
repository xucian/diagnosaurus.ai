"""Multi-agent system for medical analysis"""
from .base_agent import ResearchCapability, ReasoningCapability, BaseAgent
from .research_agent import CoarseSearchAgent, DeepResearchAgent
from .forum_coordinator import AdversarialForum
from .condition_analyzer import ConditionAnalyzer

__all__ = [
    "ResearchCapability",
    "ReasoningCapability",
    "BaseAgent",
    "CoarseSearchAgent",
    "DeepResearchAgent",
    "AdversarialForum",
    "ConditionAnalyzer",
]
