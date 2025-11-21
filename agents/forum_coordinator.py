"""
Adversarial Forum Coordinator
Manages multi-agent debate to cross-validate condition findings
"""
import asyncio
from typing import Dict, Any, List
from loguru import logger
from models.schemas import ForumDebateResult, AgentResearchResult
from .base_agent import BaseAgent, ReasoningCapability
from config import settings


class AdversarialForum(BaseAgent, ReasoningCapability):
    """
    Adversarial forum where agents debate condition probabilities
    Cross-validates findings through structured debate
    """

    def _init_capabilities(self):
        """Initialize reasoning capability"""
        ReasoningCapability.__init__(self, self.anthropic_client)

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conduct adversarial debate among research findings

        Args:
            task: {
                "research_results": List[AgentResearchResult],
                "symptoms": str,
                "patient_context": Optional[Dict]
            }

        Returns:
            {
                "debate_result": ForumDebateResult,
                "adjusted_confidences": Dict[str, float]
            }
        """
        research_results = task.get("research_results", [])
        symptoms = task.get("symptoms", "")

        logger.info(f"[{self.agent_id}] Starting adversarial forum with {len(research_results)} agents")

        # Run debate rounds
        debate_rounds = 2  # Limited for hackathon speed
        debate_history = []

        for round_num in range(debate_rounds):
            logger.info(f"[{self.agent_id}] Debate round {round_num + 1}/{debate_rounds}")

            round_result = await self._conduct_debate_round(
                research_results,
                symptoms,
                debate_history,
            )
            debate_history.append(round_result)

        # Synthesize final consensus
        consensus = await self._synthesize_consensus(research_results, debate_history)

        debate_result = ForumDebateResult(
            debate_summary=consensus.get("summary", ""),
            consensus_conditions=consensus.get("consensus_conditions", []),
            contested_points=consensus.get("contested_points", []),
            final_confidence_adjustments=consensus.get("confidence_adjustments", {}),
            participant_agents=[r.agent_id for r in research_results],
            debate_rounds=debate_rounds,
        )

        logger.info(f"[{self.agent_id}] Forum complete: {len(consensus.get('consensus_conditions', []))} consensus conditions")

        return {
            "debate_result": debate_result,
            "adjusted_confidences": consensus.get("confidence_adjustments", {}),
        }

    async def _conduct_debate_round(
        self,
        research_results: List[AgentResearchResult],
        symptoms: str,
        previous_rounds: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Conduct one round of adversarial debate"""

        # Prepare debate context
        context = self._format_research_for_debate(research_results)
        previous_context = self._format_previous_rounds(previous_rounds)

        prompt = f"""You are moderating a medical diagnostic forum. Agents have researched conditions and must now debate their findings.

Patient Symptoms: {symptoms}

Agent Research Findings:
{context}

{previous_context}

For each condition, provide:
1. SUPPORTING EVIDENCE: What supports this diagnosis?
2. CONTRADICTING EVIDENCE: What argues against it?
3. CONFIDENCE ADJUSTMENT: Should confidence increase, decrease, or stay same? (up/down/same)

Be critical and objective. Look for contradictions and weak reasoning."""

        system_prompt = """You are a senior medical diagnostician moderating a case review.
Your role is to challenge assumptions and ensure thorough differential diagnosis.
Be skeptical but fair. Focus on evidence quality."""

        response = await self.reason(prompt, system_prompt, temperature=0.6)

        # Parse debate outcomes
        return {
            "round_analysis": response,
            "challenged_conditions": self._extract_challenged_conditions(response),
        }

    async def _synthesize_consensus(
        self,
        research_results: List[AgentResearchResult],
        debate_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Synthesize final consensus from debate"""

        # Prepare debate summary
        debate_summary = "\n\n".join([r.get("round_analysis", "") for r in debate_history])

        prompt = f"""Based on the adversarial debate, provide final consensus.

Debate Summary:
{debate_summary}

Provide:
1. CONSENSUS CONDITIONS: Conditions with strong support (list condition names)
2. CONTESTED CONDITIONS: Conditions with significant debate (list condition names)
3. CONFIDENCE ADJUSTMENTS: For each researched condition, provide confidence multiplier (0.7-1.3)

Format:
CONSENSUS: [condition1], [condition2], ...
CONTESTED: [condition1], [condition2], ...
ADJUSTMENTS:
- [condition]: [multiplier]
- [condition]: [multiplier]
..."""

        response = await self.reason(prompt, temperature=0.4)

        # Parse consensus
        consensus_conditions = []
        contested_conditions = []
        confidence_adjustments = {}

        lines = response.split("\n")
        section = None

        for line in lines:
            line = line.strip()
            if line.startswith("CONSENSUS:"):
                section = "consensus"
                conditions = line.split(":", 1)[1].strip()
                consensus_conditions = [c.strip() for c in conditions.split(",") if c.strip()]
            elif line.startswith("CONTESTED:"):
                section = "contested"
                conditions = line.split(":", 1)[1].strip()
                contested_conditions = [c.strip() for c in conditions.split(",") if c.strip()]
            elif line.startswith("ADJUSTMENTS:"):
                section = "adjustments"
            elif section == "adjustments" and ":" in line:
                parts = line.split(":", 1)
                condition = parts[0].strip("- ").strip()
                try:
                    multiplier = float(parts[1].strip())
                    confidence_adjustments[condition] = multiplier
                except:
                    pass

        # Map adjustments to agent findings
        final_adjustments = {}
        for result in research_results:
            condition = result.condition_researched
            if condition in confidence_adjustments:
                # Adjust confidence
                original_confidence = result.confidence
                adjusted = original_confidence * confidence_adjustments[condition]
                final_adjustments[condition] = min(max(adjusted, 0.0), 1.0)
            else:
                final_adjustments[condition] = result.confidence

        return {
            "summary": debate_summary[:1000],
            "consensus_conditions": consensus_conditions,
            "contested_conditions": contested_conditions,
            "confidence_adjustments": final_adjustments,
            "contested_points": [
                {"condition": c, "reason": "Significant debate in forum"}
                for c in contested_conditions
            ],
        }

    def _format_research_for_debate(self, research_results: List[AgentResearchResult]) -> str:
        """Format research results for debate context"""
        formatted = []
        for result in research_results:
            formatted.append(
                f"Agent {result.agent_id}:\n"
                f"  Condition: {result.condition_researched}\n"
                f"  Confidence: {result.confidence:.2f}\n"
                f"  Findings: {result.findings[:200]}...\n"
                f"  Sources: {', '.join(result.sources[:3])}\n"
            )
        return "\n".join(formatted)

    def _format_previous_rounds(self, previous_rounds: List[Dict[str, Any]]) -> str:
        """Format previous debate rounds"""
        if not previous_rounds:
            return ""

        return f"\nPrevious Debate Rounds:\n" + "\n".join([
            f"Round {i+1}: {r.get('round_analysis', '')[:200]}..."
            for i, r in enumerate(previous_rounds)
        ])

    def _extract_challenged_conditions(self, debate_text: str) -> List[str]:
        """Extract conditions that were challenged in debate"""
        challenged = []
        for line in debate_text.split("\n"):
            if "contradicting evidence" in line.lower() or "argues against" in line.lower():
                # Extract condition name (simplified)
                words = line.split()
                for word in words:
                    if len(word) > 5 and word[0].isupper():
                        challenged.append(word)
        return list(set(challenged))
