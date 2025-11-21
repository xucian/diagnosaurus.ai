#!/usr/bin/env python3
"""
Test research service functionality

Tests both Parallel.ai and fallback (DuckDuckGo) research
"""
import sys
import asyncio
from config import settings
from services.parallel_service import get_research_service


async def test_service_selection():
    """Test that correct service is selected based on config"""

    print("Testing Service Selection")
    print("=" * 60)

    service = get_research_service()
    service_type = type(service).__name__

    expected = "FallbackResearchService" if settings.use_fallback_research else "ParallelService"
    success = service_type == expected

    print(f"\n{'✓ PASS' if success else '✗ FAIL'} - Service selection")
    print(f"  USE_FALLBACK_RESEARCH: {settings.use_fallback_research}")
    print(f"  Expected: {expected}")
    print(f"  Got: {service_type}")

    return success


async def test_medical_search():
    """Test basic medical search"""

    print("\n" + "=" * 60)
    print("Testing Medical Search")
    print("=" * 60)

    service = get_research_service()

    print(f"\nUsing: {type(service).__name__}")
    print("Query: 'iron deficiency anemia symptoms'")

    try:
        results = await service.search_medical(
            query="iron deficiency anemia symptoms",
            max_results=3
        )

        success = len(results) > 0

        print(f"\n{'✓ PASS' if success else '✗ FAIL'} - Medical search")
        print(f"  Found {len(results)} results")

        if results:
            print(f"\n  Sample result:")
            print(f"    Content: {results[0].get('content', 'N/A')[:150]}...")
            print(f"    Citation: {results[0].get('citation', 'N/A')}")

        return success

    except Exception as e:
        print(f"\n✗ FAIL - Medical search")
        print(f"  Error: {e}")
        return False


async def test_clinic_search():
    """Test clinic discovery"""

    print("\n" + "=" * 60)
    print("Testing Clinic Search")
    print("=" * 60)

    service = get_research_service()

    # San Francisco coordinates
    location = {"lat": 37.7749, "lon": -122.4194}

    print(f"\nSearching near: {location}")

    try:
        clinics = await service.find_clinics(
            location=location,
            specialty="internal medicine",
            min_rating=3.5
        )

        success = isinstance(clinics, list)  # May be empty, that's ok

        print(f"\n{'✓ PASS' if success else '✗ FAIL'} - Clinic search")
        print(f"  Found {len(clinics)} clinics")

        if clinics:
            clinic = clinics[0]
            print(f"\n  Sample clinic:")
            print(f"    Name: {clinic.name}")
            print(f"    Rating: {clinic.rating}")
            print(f"    Distance: {clinic.distance_km:.1f} km")

        return success

    except Exception as e:
        print(f"\n✗ FAIL - Clinic search")
        print(f"  Error: {e}")
        return False


async def test_condition_research():
    """Test deep condition research"""

    print("\n" + "=" * 60)
    print("Testing Condition Research")
    print("=" * 60)

    service = get_research_service()

    condition = "Iron deficiency anemia"
    symptoms = "fatigue, pale skin, dizziness"

    print(f"\nCondition: {condition}")
    print(f"Symptoms context: {symptoms}")

    try:
        research = await service.research_condition(
            condition_name=condition,
            symptom_context=symptoms
        )

        success = (
            research.get("condition") == condition and
            len(research.get("overview", "")) > 0
        )

        print(f"\n{'✓ PASS' if success else '✗ FAIL'} - Condition research")
        print(f"  Overview length: {len(research.get('overview', ''))} chars")
        print(f"  Symptoms found: {len(research.get('symptoms', []))}")
        print(f"  Sources: {len(research.get('sources', []))}")

        if success:
            print(f"\n  Overview preview:")
            print(f"    {research['overview'][:200]}...")

        return success

    except Exception as e:
        print(f"\n✗ FAIL - Condition research")
        print(f"  Error: {e}")
        return False


async def run_all_tests():
    """Run all async tests"""

    print("Research Service Tests")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  USE_FALLBACK_RESEARCH: {settings.use_fallback_research}")
    print(f"  FALLBACK_BROWSER: {settings.fallback_browser if settings.use_fallback_research else 'N/A'}")
    print()

    results = [
        await test_service_selection(),
        await test_medical_search(),
        await test_clinic_search(),
        await test_condition_research(),
    ]

    print("\n" + "=" * 60)

    # Summary
    passed = sum(results)
    total = len(results)

    if all(results):
        print(f"✓ ALL TESTS PASSED ({passed}/{total})")
        return True
    else:
        print(f"✗ SOME TESTS FAILED ({passed}/{total} passed)")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
