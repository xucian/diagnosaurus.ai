#!/usr/bin/env python3
"""
Test full analysis pipeline

End-to-end test of the complete multi-agent system
"""
import sys
import asyncio
from datetime import datetime
from models.schemas import SymptomAnalysisRequest, Location
from services.redis_service import RedisService
from services.skyflow_service import skyflow_service
from services.parallel_service import get_research_service
from services.document_service import document_service
from agents.research_agent import CoarseSearchAgent, DeepResearchAgent
from agents.forum_coordinator import AdversarialForum
from agents.condition_analyzer import condition_analyzer


async def test_minimal_pipeline():
    """Test pipeline with minimal data (no documents)"""

    print("Testing Minimal Pipeline")
    print("=" * 60)

    # Simple symptom request
    request = SymptomAnalysisRequest(
        symptoms="Persistent fatigue, dizziness, and pale skin for 2 weeks. Feel weak when standing up.",
        patient_age=35,
        patient_sex="female",
        location=Location(latitude=37.7749, longitude=-122.4194, city="San Francisco")
    )

    print(f"\nSymptoms: {request.symptoms[:80]}...")
    print(f"Patient: {request.patient_age}yo {request.patient_sex}")

    try:
        # Step 1: PII sanitization
        print("\n[1/5] Sanitizing text...")
        sanitized = skyflow_service.sanitize_text(request.symptoms)
        print(f"  ✓ Sanitized {len(request.symptoms)} → {len(sanitized)} chars")

        # Step 2: Coarse search
        print("\n[2/5] Coarse search (identifying conditions)...")
        research_service = get_research_service()
        coarse_agent = CoarseSearchAgent(parallel_service=research_service)

        coarse_result = await coarse_agent.execute({
            "symptoms": sanitized,
            "patient_context": {"age": request.patient_age, "sex": request.patient_sex}
        })

        conditions = coarse_result["conditions"]
        print(f"  ✓ Identified {len(conditions)} potential conditions")
        print(f"    {', '.join(conditions[:3])}")

        # Step 3: Deep research (just first 2 for speed)
        print("\n[3/5] Deep research (investigating conditions)...")
        research_results = []

        for condition in conditions[:2]:  # Limit to 2 for quick test
            agent = DeepResearchAgent(parallel_service=research_service)
            result = await agent.execute({
                "condition": condition,
                "symptoms": sanitized,
                "patient_context": {"age": request.patient_age, "sex": request.patient_sex}
            })
            research_results.append(result["research_result"])
            print(f"  ✓ Researched: {condition}")

        # Step 4: Adversarial forum
        print("\n[4/5] Adversarial forum (cross-validation)...")
        forum = AdversarialForum()
        forum_result = await forum.execute({
            "research_results": research_results,
            "symptoms": sanitized,
            "patient_context": {"age": request.patient_age, "sex": request.patient_sex}
        })
        print(f"  ✓ Debate complete, {len(forum_result['adjusted_confidences'])} confidence scores")

        # Step 5: Final analysis
        print("\n[5/5] Final condition scoring...")
        final_conditions = condition_analyzer.analyze(
            research_results,
            forum_result["adjusted_confidences"],
            sanitized
        )
        print(f"  ✓ {len(final_conditions)} conditions passed filters")

        # Results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        for i, cond in enumerate(final_conditions, 1):
            print(f"\n{i}. {cond.name}")
            print(f"   Probability: {cond.probability:.1%}")
            print(f"   Confidence:  {cond.confidence:.1%}")
            print(f"   Urgency:     {cond.urgency}")
            print(f"   Evidence:    {cond.evidence_summary[:100]}...")

        success = len(final_conditions) > 0

        print("\n" + "=" * 60)
        print(f"{'✓ PASS' if success else '✗ FAIL'} - Pipeline completed")

        return success

    except Exception as e:
        print(f"\n✗ FAIL - Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_document():
    """Test pipeline with document upload"""

    print("\n\n" + "=" * 60)
    print("Testing Pipeline with Document")
    print("=" * 60)

    # Create mock PDF
    import base64
    mock_pdf = base64.b64encode(b"Mock blood work: Hemoglobin 8.2 g/dL").decode()

    request = SymptomAnalysisRequest(
        symptoms="Fatigue and pale skin",
        documents=[mock_pdf],
        patient_age=30,
        patient_sex="female"
    )

    print(f"\nSymptoms: {request.symptoms}")
    print(f"Documents: {len(request.documents)}")

    try:
        # Extract and merge
        print("\n[1/2] Extracting document text...")
        doc_text = document_service.extract_text_from_documents(request.documents)
        combined = request.symptoms + "\n\n--- Medical Documents ---\n" + doc_text
        print(f"  ✓ Combined text: {len(combined)} chars")

        # Sanitize
        print("\n[2/2] Sanitizing combined text...")
        sanitized = skyflow_service.sanitize_text(combined)
        print(f"  ✓ Sanitized: {len(sanitized)} chars")

        success = len(sanitized) >= len(request.symptoms)

        print(f"\n{'✓ PASS' if success else '✗ FAIL'} - Document processing")

        return success

    except Exception as e:
        print(f"\n✗ FAIL - Document processing error: {e}")
        return False


async def test_redis_integration():
    """Test Redis session storage"""

    print("\n\n" + "=" * 60)
    print("Testing Redis Integration")
    print("=" * 60)

    try:
        redis = RedisService()

        # Health check
        print("\n[1/3] Redis health check...")
        healthy = redis.health_check()
        print(f"  {'✓' if healthy else '✗'} Redis connection")

        if not healthy:
            print("  ⚠️  Redis not running. Start with: docker-compose up -d")
            return False

        # Store session
        print("\n[2/3] Storing session data...")
        session_id = "test_session_123"
        data = {
            "status": "testing",
            "timestamp": datetime.utcnow().isoformat()
        }
        redis.set_session_data(session_id, data, ttl=60)
        print(f"  ✓ Stored session: {session_id}")

        # Retrieve session
        print("\n[3/3] Retrieving session data...")
        retrieved = redis.get_session_data(session_id)
        success = retrieved and retrieved["status"] == "testing"
        print(f"  {'✓' if success else '✗'} Retrieved and verified")

        return success

    except Exception as e:
        print(f"\n✗ FAIL - Redis error: {e}")
        return False


async def run_all_tests():
    """Run all pipeline tests"""

    print("Full Pipeline Tests")
    print("=" * 60)
    print(f"Started: {datetime.utcnow().isoformat()}")
    print()

    results = [
        await test_redis_integration(),
        await test_with_document(),
        await test_minimal_pipeline(),
    ]

    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if all(results):
        print("✓ ALL TESTS PASSED")
        return True
    else:
        print("✗ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    print("⚠️  WARNING: This test makes real API calls and may take 1-2 minutes")
    print("⚠️  Ensure Redis is running: docker-compose up -d")
    print("⚠️  Ensure API keys in .env: ANTHROPIC_API_KEY, PARALLEL_AI_API_KEY")
    print("\nPress Ctrl+C to cancel, or wait 3 seconds to continue...")

    try:
        import time
        time.sleep(3)

        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nTests cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
