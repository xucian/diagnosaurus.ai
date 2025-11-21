"""
Pydantic schemas for Diagnosaurus.ai
Type-safe data models with validation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class Location(BaseModel):
    """Geographic location"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    city: Optional[str] = None
    country: Optional[str] = None
    ip_address: Optional[str] = None


class SymptomAnalysisRequest(BaseModel):
    """Request payload for symptom analysis"""
    symptoms: str = Field(..., min_length=10, description="Patient symptom description")
    documents: List[str] = Field(default_factory=list, description="Base64 encoded medical documents")
    location: Optional[Location] = None
    patient_age: Optional[int] = Field(None, ge=0, le=120)
    patient_sex: Optional[str] = Field(None, pattern="^(male|female|other)$")
    medical_history: Optional[str] = None

    @validator("symptoms")
    def validate_symptoms(cls, v):
        """Ensure symptoms are meaningful"""
        if len(v.strip()) < 10:
            raise ValueError("Symptom description too short")
        return v.strip()


class ConditionEvidence(BaseModel):
    """Evidence supporting a medical condition"""
    source: str = Field(..., description="Evidence source (LLM/Parallel.ai/Forum)")
    content: str = Field(..., description="Evidence text")
    relevance_score: float = Field(..., ge=0, le=1, description="How relevant to condition")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MedicalCondition(BaseModel):
    """Analyzed medical condition with probability"""
    name: str = Field(..., description="Condition name")
    probability: float = Field(..., ge=0, le=1, description="Likelihood (0-1)")
    confidence: float = Field(..., ge=0, le=1, description="Agent confidence in assessment")
    body_region: str = Field(..., description="Affected body region")
    evidence_summary: str = Field(..., description="Key evidence synopsis")
    evidence_details: List[ConditionEvidence] = Field(default_factory=list)
    position: Dict[str, int] = Field(..., description="UI position {x, y}")
    symptoms_matched: List[str] = Field(default_factory=list)
    recommended_tests: List[str] = Field(default_factory=list)
    urgency: str = Field(default="routine", pattern="^(emergency|urgent|routine|monitor)$")

    @validator("probability", "confidence")
    def validate_scores(cls, v):
        """Ensure scores are valid probabilities"""
        if not 0 <= v <= 1:
            raise ValueError("Score must be between 0 and 1")
        return v


class ClinicResult(BaseModel):
    """Clinic search result"""
    name: str = Field(..., description="Clinic/provider name")
    doctor_name: str = Field(..., description="Doctor full name")
    specialty: str = Field(..., description="Medical specialty")
    rating: float = Field(..., ge=0, le=5, description="Google rating (0-5)")
    review_count: int = Field(..., ge=0, description="Number of reviews")
    phone: str = Field(..., description="Contact phone number")
    address: str = Field(..., description="Physical address")
    distance_km: float = Field(..., ge=0, description="Distance from user")
    accepts_new_patients: bool = Field(default=True)
    website: Optional[str] = None
    next_available: Optional[str] = Field(None, description="Next appointment slot")

    @property
    def doctor_last_name_blurred(self) -> str:
        """Return doctor name with last name blurred"""
        parts = self.doctor_name.split()
        if len(parts) > 1:
            return f"{parts[0]} {parts[-1][0]}***"
        return self.doctor_name


class AgentResearchResult(BaseModel):
    """Result from individual agent research"""
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Agent type (coarse/deep)")
    condition_researched: Optional[str] = None
    findings: str = Field(..., description="Research findings")
    sources: List[str] = Field(default_factory=list, description="Information sources")
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str = Field(..., description="Agent reasoning process")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = Field(..., ge=0)


class ForumDebateResult(BaseModel):
    """Result from adversarial forum debate"""
    debate_summary: str = Field(..., description="Debate outcome summary")
    consensus_conditions: List[str] = Field(..., description="Agreed-upon conditions")
    contested_points: List[Dict[str, Any]] = Field(default_factory=list)
    final_confidence_adjustments: Dict[str, float] = Field(default_factory=dict)
    participant_agents: List[str] = Field(..., description="Agent IDs in debate")
    debate_rounds: int = Field(..., ge=1)


class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    session_id: str = Field(..., description="Analysis session ID")
    conditions: List[MedicalCondition] = Field(..., description="Analyzed conditions")
    clinics: List[ClinicResult] = Field(default_factory=list, description="Nearby clinics")
    agent_research: List[AgentResearchResult] = Field(default_factory=list)
    forum_debate: Optional[ForumDebateResult] = None
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = Field(..., ge=0)
    warning_message: Optional[str] = Field(None, description="General symptom warning")

    @validator("conditions")
    def validate_conditions(cls, v):
        """Ensure conditions are sorted by probability"""
        return sorted(v, key=lambda x: x.probability, reverse=True)


class AgentStatus(BaseModel):
    """Real-time agent execution status"""
    agent_id: str
    agent_type: str
    status: str = Field(..., pattern="^(pending|running|completed|failed)$")
    current_task: Optional[str] = None
    progress_percent: int = Field(default=0, ge=0, le=100)
    message: Optional[str] = None


class SessionStatus(BaseModel):
    """Analysis session status for polling"""
    session_id: str
    overall_status: str = Field(..., pattern="^(initializing|researching|debating|analyzing|completed|failed)$")
    progress_percent: int = Field(default=0, ge=0, le=100)
    agents: List[AgentStatus] = Field(default_factory=list)
    current_phase: str
    estimated_time_remaining_seconds: Optional[int] = None
    result: Optional[AnalysisResponse] = None
    error: Optional[str] = None
