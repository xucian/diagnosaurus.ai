#!/usr/bin/env python3
"""
Quick test to verify Parallel SDK installation and API
"""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from parallel import Parallel

    api_key = os.getenv("PARALLEL_AI_API_KEY")
    if not api_key:
        print("❌ PARALLEL_AI_API_KEY not set in .env")
        exit(1)

    print(f"✓ Parallel SDK imported successfully")
    print(f"✓ API key loaded: {api_key[:20]}...")

    client = Parallel(api_key=api_key)
    print(f"✓ Parallel client created")

    # Test search
    response = client.beta.search(
        mode="one-shot",
        max_results=3,
        objective="iron deficiency anemia symptoms"
    )

    print(f"\n✓ Search successful!")
    print(f"  Found {len(response.results)} results")
    print(f"\n  First result:")
    print(f"    Title: {response.results[0].title}")
    print(f"    URL: {response.results[0].url}")
    print(f"    Excerpt: {response.results[0].excerpts[0][:200]}...")

except ImportError as e:
    print(f"❌ Failed to import Parallel SDK")
    print(f"   Error: {e}")
    print(f"\n   Installation needed:")
    print(f"   Please provide the installation command for the Parallel SDK")
    exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
