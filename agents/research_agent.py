"""
Research agents for medical symptom analysis
- CoarseSearchAgent: High-level condition identification
- DeepResearchAgent: Detailed condition investigation
"""
import time
from typing import Dict, Any, List, Optional
from loguru import logger
from config import settings
from models.schemas import AgentResearchResult
from .base_agent import BaseAgent, ResearchCapability, ReasoningCapability


class CoarseSearchAgent(BaseAgent, ResearchCapability, ReasoningCapability):
    """
    Phase 1 Agent: Coarse-grained search for potential medical conditions
    Identifies MAX_CONDITIONS possible diagnoses from symptoms
    """

    def _init_capabilities(self):
        """Initialize research and reasoning capabilities"""
        ResearchCapability.__init__(self, self.parallel_service)
        ReasoningCapability.__init__(self, self.anthropic_client)

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute coarse search to identify potential conditions

        Args:
            task: {"symptoms": str, "patient_context": Optional[Dict]}

        Returns:
            {"conditions": List[str], "reasoning": str, "research_result": AgentResearchResult}
        """
        start_time = time.time()
        symptoms = task.get("symptoms", "")
        patient_context = task.get("patient_context", {})

        logger.info(f"[{self.agent_id}] Starting coarse search for symptoms")

        # Step 1: LLM intuition pass (no tools)
        intuition_conditions = await self._llm_intuition_search(symptoms, patient_context)

        # Step 2: Parallel.ai research pass
        research_conditions = await self._parallel_research_search(symptoms)

        # Step 3: Synthesize results
        final_conditions = self._synthesize_conditions(
            intuition_conditions,
            research_conditions,
        )

        # Limit to MAX_CONDITIONS
        final_conditions = final_conditions[:settings.max_conditions]

        processing_time = int((time.time() - start_time) * 1000)

        research_result = AgentResearchResult(
            agent_id=self.agent_id,
            agent_type="coarse_search",
            condition_researched=None,
            findings=f"Identified {len(final_conditions)} potential conditions",
            sources=["LLM reasoning", "Parallel.ai medical search"],
            confidence=0.7,  # Initial confidence for coarse search
            reasoning=f"Combined LLM intuition with medical literature search",
            processing_time_ms=processing_time,
        )

        logger.info(f"[{self.agent_id}] Coarse search complete: {final_conditions}")

        return {
            "conditions": final_conditions,
            "reasoning": research_result.reasoning,
            "research_result": research_result,
        }

    async def _llm_intuition_search(
        self,
        symptoms: str,
        patient_context: Dict[str, Any],
    ) -> List[str]:
        """LLM-only reasoning about potential conditions"""
        context_str = ""
        if patient_context.get("age"):
            context_str += f"Age: {patient_context['age']}\n"
        if patient_context.get("sex"):
            context_str += f"Sex: {patient_context['sex']}\n"

        prompt = f"""You are a medical diagnostician. Based on these symptoms, identify {settings.max_conditions * 2} possible medical conditions (cast a wide net).

{context_str}
Symptoms: {symptoms}

Return ONLY a numbered list of condition names, no explanations:
1. [Condition name]
2. [Condition name]
..."""

        system_prompt = """You are an expert medical diagnostician with 20+ years of experience.
You excel at differential diagnosis - considering all possibilities before narrowing down.
Be thorough but precise in identifying potential conditions."""

        response = await self.reason(prompt, system_prompt, temperature=0.7)

        # Parse condition list
        conditions = []
        for line in response.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Extract condition name
                condition = line.split(".", 1)[-1].split("-", 1)[-1].strip()
                if condition:
                    conditions.append(condition)

        logger.debug(f"LLM intuition identified {len(conditions)} conditions")
        return conditions[:settings.max_conditions * 2]

    async def _parallel_research_search(self, symptoms: str) -> List[str]:
        """Parallel.ai research for conditions"""
        try:
            query = f"Medical conditions with symptoms: {symptoms[:300]}"
            results = await self.research_web(
                query=query,
                sources=["medical", "pubmed", "mayo_clinic"],
            )

            # Extract condition names from research
            conditions = []
            for result in results:
                content = result.get("content", "")
                # Simple extraction - look for condition names in titles/headings
                if "condition" in content.lower() or "disease" in content.lower():
                    # Extract potential condition names (this is simplified)
                    lines = content.split("\n")
                    for line in lines[:5]:  # Check first few lines
                        if line.strip() and len(line) < 100:
                            conditions.append(line.strip())

            logger.debug(f"Parallel.ai research found {len(conditions)} potential conditions")
            return conditions[:settings.max_conditions]

        except Exception as e:
            logger.error(f"Parallel.ai search failed: {e}")
            return []

    def _synthesize_conditions(
        self,
        intuition: List[str],
        research: List[str],
    ) -> List[str]:
        """Combine and deduplicate conditions from both sources"""
        # Combine both lists
        all_conditions = intuition + research

        # Deduplicate (case-insensitive)
        seen = set()
        unique_conditions = []
        for condition in all_conditions:
            condition_lower = condition.lower().strip()
            if condition_lower not in seen:
                seen.add(condition_lower)
                unique_conditions.append(condition)

        # Prioritize conditions that appear in both sources
        high_priority = [c for c in unique_conditions if c in intuition and c in research]
        medium_priority = [c for c in unique_conditions if c in intuition or c in research]

        # Combine with high priority first
        final = high_priority + [c for c in medium_priority if c not in high_priority]

        return final[:settings.max_conditions * 2]  # Return extras for filtering later


class DeepResearchAgent(BaseAgent, ResearchCapability, ReasoningCapability):
    """
    Phase 2 Agent: Deep research on specific condition
    Investigates one condition in detail
    """

    def _init_capabilities(self):
        """Initialize research and reasoning capabilities"""
        ResearchCapability.__init__(self, self.parallel_service)
        ReasoningCapability.__init__(self, self.anthropic_client)

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute deep research on a specific condition

        Args:
            task: {
                "condition": str,
                "symptoms": str,
                "patient_context": Optional[Dict]
            }

        Returns:
            {
                "condition": str,
                "evidence": Dict[str, Any],
                "confidence": float,
                "research_result": AgentResearchResult
            }
        """
        start_time = time.time()
        condition = task.get("condition", "")
        symptoms = task.get("symptoms", "")
        patient_context = task.get("patient_context", {})

        logger.info(f"[{self.agent_id}] Deep research on: {condition}")

        # Sub-search 1: LLM intuition about this specific condition
        intuition = await self._llm_condition_analysis(condition, symptoms, patient_context)

        # Sub-search 2: Parallel.ai detailed research
        research = await self.research_condition_details(condition, symptoms)

        # Synthesize evidence
        evidence = self._synthesize_evidence(intuition, research, symptoms)

        processing_time = int((time.time() - start_time) * 1000)

        research_result = AgentResearchResult(
            agent_id=self.agent_id,
            agent_type="deep_research",
            condition_researched=condition,
            findings=evidence.get("summary", ""),
            sources=evidence.get("sources", []),
            confidence=evidence.get("confidence", 0.5),
            reasoning=evidence.get("reasoning", ""),
            processing_time_ms=processing_time,
        )

        logger.info(f"[{self.agent_id}] Deep research complete for {condition}")

        return {
            "condition": condition,
            "evidence": evidence,
            "confidence": evidence.get("confidence", 0.5),
            "research_result": research_result,
        }

    async def _llm_condition_analysis(
        self,
        condition: str,
        symptoms: str,
        patient_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """LLM analysis of condition match with symptoms"""
        prompt = f"""Analyze how well this condition matches the patient's symptoms.

Condition: {condition}
Symptoms: {symptoms}

Provide:
1. Probability this condition matches symptoms (0.0-1.0)
2. Key symptoms that match
3. Key symptoms that don't match
4. Your reasoning

Format as:
PROBABILITY: [0.0-1.0]
MATCHES: [list]
MISMATCHES: [list]
REASONING: [explanation]"""

        system_prompt = """You are a medical expert evaluating diagnostic hypotheses.
Be objective and evidence-based. Consider both positive and negative evidence."""

        response = await self.reason(prompt, system_prompt, temperature=0.5)

        # Parse response
        probability = 0.5
        matches = []
        reasoning = response

        for line in response.split("\n"):
            if line.startswith("PROBABILITY:"):
                try:
                    probability = float(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("MATCHES:"):
                matches = [m.strip() for m in line.split(":")[1].split(",")]

        return {
            "probability": probability,
            "matched_symptoms": matches,
            "reasoning": reasoning,
            "source": "LLM intuition",
        }

    def _synthesize_evidence(
        self,
        intuition: Dict[str, Any],
        research: Dict[str, Any],
        symptoms: str,
    ) -> Dict[str, Any]:
        """Combine LLM intuition and research into structured evidence"""
        # Calculate weighted confidence
        llm_prob = intuition.get("probability", 0.5)
        research_quality = min(len(research.get("sources", [])) / 5.0, 1.0)

        # Weight: 60% LLM, 40% research quality
        confidence = (llm_prob * 0.6) + (research_quality * 0.4)

        return {
            "condition": research.get("condition", ""),
            "probability": llm_prob,
            "confidence": confidence,
            "matched_symptoms": intuition.get("matched_symptoms", []),
            "summary": research.get("overview", "")[:500],
            "detailed_symptoms": research.get("symptoms", []),
            "causes": research.get("causes", []),
            "risk_factors": research.get("risk_factors", []),
            "sources": research.get("sources", []) + ["LLM analysis"],
            "reasoning": intuition.get("reasoning", ""),
        }
