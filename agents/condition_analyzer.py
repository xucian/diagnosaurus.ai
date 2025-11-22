"""
Condition Analyzer
Final scoring and filtering of conditions based on forum results
"""
from typing import List, Dict, Any
from loguru import logger
from config import settings, BODY_REGIONS
from models.schemas import MedicalCondition, ConditionEvidence, AgentResearchResult


class ConditionAnalyzer:
    """
    Analyzes and scores conditions after forum debate
    Applies filtering rules and prepares final output
    """

    def __init__(self):
        logger.info("ConditionAnalyzer initialized")

    def analyze(
        self,
        research_results: List[AgentResearchResult],
        adjusted_confidences: Dict[str, float],
        symptoms: str,
    ) -> List[MedicalCondition]:
        """
        Analyze and score all researched conditions

        Args:
            research_results: Agent research outputs
            adjusted_confidences: Confidence scores from forum
            symptoms: Original symptoms for context

        Returns:
            List of MedicalCondition objects, filtered and scored
        """
        logger.info(f"Analyzing {len(research_results)} conditions")

        conditions = []

        for result in research_results:
            if not result.condition_researched:
                continue

            condition = self._create_condition_from_research(
                result,
                adjusted_confidences.get(result.condition_researched, result.confidence),
                symptoms,
            )

            # Apply filtering rules
            if self._should_include_condition(condition):
                conditions.append(condition)

        # Sort by probability (descending)
        conditions.sort(key=lambda c: c.probability, reverse=True)

        # Limit to MAX_CONDITIONS
        conditions = conditions[:settings.max_conditions]

        # Check if symptoms are too general
        if self._are_symptoms_too_general(symptoms, conditions):
            logger.warning("Symptoms may be too general - adding warning")
            # Lower all probabilities slightly
            for condition in conditions:
                condition.probability *= 0.8

        logger.info(f"Analysis complete: {len(conditions)} conditions passed filters")
        return conditions

    def _create_condition_from_research(
        self,
        research: AgentResearchResult,
        final_confidence: float,
        symptoms: str,
    ) -> MedicalCondition:
        """Create MedicalCondition from research result"""

        # Extract probability from findings (or use confidence as fallback)
        probability = self._extract_probability(research.findings) or final_confidence or 0.70  # Default to 70% if no data

        # Determine body region
        body_region = self._infer_body_region(research.condition_researched)

        # Get UI position
        position = BODY_REGIONS.get(body_region, BODY_REGIONS["general"])

        # Create evidence details
        evidence_details = [
            ConditionEvidence(
                source=research.agent_type,
                content=research.findings[:500],
                relevance_score=final_confidence,
            )
        ]

        # Determine urgency
        urgency = self._assess_urgency(
            research.condition_researched,
            probability,
            final_confidence,
        )

        return MedicalCondition(
            name=research.condition_researched,
            probability=probability,
            confidence=final_confidence,
            body_region=body_region,
            evidence_summary=research.findings[:300],
            evidence_details=evidence_details,
            position=position,
            symptoms_matched=self._extract_matched_symptoms(research.reasoning),
            recommended_tests=self._suggest_tests(research.condition_researched),
            urgency=urgency,
        )

    def _should_include_condition(self, condition: MedicalCondition) -> bool:
        """
        DEMO MODE: Simplified filtering to ensure conditions show up
        Just filter out obviously invalid conditions
        """
        if condition.probability == 0 and condition.confidence == 0:
            return False
        # Allow all conditions with any probability/confidence > 0
        return True

    def _extract_probability(self, findings_text: str) -> float:
        """Extract probability score from findings text"""
        # Look for probability indicators in text
        findings_lower = findings_text.lower()

        if "probability" in findings_lower:
            # Try to extract numeric value
            import re
            match = re.search(r'probability[:\s]+([0-9.]+)', findings_lower)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass

        # Fallback: return None to use confidence
        return None

    def _infer_body_region(self, condition_name: str) -> str:
        """Infer body region from condition name"""
        condition_lower = condition_name.lower()

        # Simple keyword matching
        region_keywords = {
            "head": ["headache", "migraine", "concussion"],
            "brain": ["alzheimer", "dementia", "stroke", "seizure"],
            "heart": ["heart", "cardiac", "cardiovascular", "arrhythmia"],
            "lungs": ["lung", "pneumonia", "asthma", "bronchitis"],
            "respiratory": ["respiratory", "breathing"],
            "stomach": ["stomach", "gastric", "ulcer"],
            "liver": ["liver", "hepatitis", "cirrhosis"],
            "kidneys": ["kidney", "renal"],
            "digestive": ["digestive", "intestinal", "bowel", "ibs"],
            "blood": ["anemia", "leukemia", "blood"],
            "immune": ["immune", "autoimmune", "lupus"],
            "endocrine": ["diabetes", "thyroid", "hormone"],
            "musculoskeletal": ["arthritis", "bone", "joint", "muscle"],
            "skin": ["skin", "dermatitis", "rash"],
        }

        for region, keywords in region_keywords.items():
            if any(keyword in condition_lower for keyword in keywords):
                return region

        return "general"

    def _extract_matched_symptoms(self, reasoning_text: str) -> List[str]:
        """Extract matched symptoms from reasoning"""
        # Look for "MATCHES:" section
        if "MATCHES:" in reasoning_text:
            matches_section = reasoning_text.split("MATCHES:")[1].split("\n")[0]
            symptoms = [s.strip() for s in matches_section.split(",")]
            return symptoms[:5]  # Top 5 matched symptoms

        return []

    def _suggest_tests(self, condition_name: str) -> List[str]:
        """Suggest diagnostic tests for condition (simplified)"""
        condition_lower = condition_name.lower()

        test_mappings = {
            "anemia": ["Complete Blood Count (CBC)", "Iron levels", "Ferritin test"],
            "diabetes": ["Fasting blood glucose", "HbA1c test", "Oral glucose tolerance test"],
            "thyroid": ["TSH test", "Free T4", "Thyroid antibodies"],
            "heart": ["ECG", "Echocardiogram", "Stress test", "Cardiac enzymes"],
            "liver": ["Liver function tests", "Ultrasound", "Bilirubin test"],
            "kidney": ["Creatinine test", "BUN", "Urinalysis", "GFR"],
        }

        for key, tests in test_mappings.items():
            if key in condition_lower:
                return tests

        return ["Physical examination", "Medical history review", "Targeted lab work"]

    def _assess_urgency(
        self,
        condition_name: str,
        probability: float,
        confidence: float,
    ) -> str:
        """Assess urgency level for condition"""
        condition_lower = condition_name.lower()

        # Emergency conditions
        emergency_keywords = ["stroke", "heart attack", "aneurysm", "sepsis", "meningitis"]
        if any(keyword in condition_lower for keyword in emergency_keywords):
            return "emergency"

        # Urgent conditions
        urgent_keywords = ["infection", "pneumonia", "acute", "severe"]
        if any(keyword in condition_lower for keyword in urgent_keywords):
            if probability > 0.6 or confidence > 0.7:
                return "urgent"

        # High probability/confidence = urgent
        if probability > 0.8 and confidence > 0.8:
            return "urgent"

        # Monitor conditions (low probability/confidence)
        if probability < 0.3 or confidence < 0.5:
            return "monitor"

        return "routine"

    def _are_symptoms_too_general(
        self,
        symptoms: str,
        conditions: List[MedicalCondition],
    ) -> bool:
        """Check if symptoms are too general to be reliable"""
        symptoms_lower = symptoms.lower()

        # Very general symptoms
        general_symptoms = ["tired", "fatigue", "pain", "headache", "dizzy"]
        symptom_count = sum(1 for s in general_symptoms if s in symptoms_lower)

        # If mostly general symptoms and low confidence, flag as too general
        if symptom_count >= 2:
            avg_confidence = sum(c.confidence for c in conditions) / len(conditions) if conditions else 0
            if avg_confidence < 0.6:
                return True

        return False


# Global instance
condition_analyzer = ConditionAnalyzer()
