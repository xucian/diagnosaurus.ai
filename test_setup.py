#!/usr/bin/env python3
"""
Quick setup validation script
Checks that all dependencies and services are properly configured
"""

import sys
import importlib
from pathlib import Path


def check_python_version():
    """Check Python version is 3.11+"""
    print("Checking Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (need 3.11+)")
        return False


def check_dependencies():
    """Check if all required packages are installed"""
    print("\nChecking dependencies...")

    required = [
        "flask",
        "anthropic",
        "redis",
        "redisvl",
        "skyflow",
        "pypdf",
        "pydantic",
        "loguru",
        "httpx",
    ]

    all_ok = True
    for package in required:
        try:
            importlib.import_module(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ❌ {package} not installed")
            all_ok = False

    return all_ok


def check_env_file():
    """Check if .env file exists"""
    print("\nChecking configuration...", end=" ")
    env_path = Path(".env")

    if env_path.exists():
        print("✓ .env file exists")

        # Check for required keys
        with open(env_path) as f:
            content = f.read()

        required_keys = [
            "ANTHROPIC_API_KEY",
            "PARALLEL_AI_API_KEY",
        ]

        missing = []
        for key in required_keys:
            if key not in content or f"{key}=your_" in content or f"{key}=sk-ant-api03-..." in content:
                missing.append(key)

        if missing:
            print(f"  ⚠️  Missing or placeholder values for: {', '.join(missing)}")
            return False
        else:
            print("  ✓ All required API keys configured")

            # Check optional Skyflow
            if "SKYFLOW_VAULT_ID" in content and not content.startswith("#"):
                print("  ✓ Skyflow configured (optional)")
            else:
                print("  ℹ️  Skyflow not configured (will use regex fallback)")

            return True
    else:
        print("❌ .env file not found")
        print("  Run: cp .env.example .env")
        return False


def check_directories():
    """Check if required directories exist"""
    print("\nChecking directories...", end=" ")

    required_dirs = [
        "agents",
        "services",
        "models",
        "templates",
        "static",
        "data",
        "uploads",
    ]

    all_ok = True
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            print(f"❌ {dir_name}/ missing")
            all_ok = False

    if all_ok:
        print("✓ All directories present")

    return all_ok


def check_redis():
    """Check if Redis is accessible"""
    print("\nChecking Redis connection...", end=" ")

    try:
        import redis
        client = redis.Redis(host='localhost', port=6380, db=0, socket_timeout=2)
        client.ping()
        print("✓ Redis is running")
        return True
    except Exception as e:
        print(f"❌ Redis not accessible: {e}")
        print("  Run: docker-compose up -d")
        return False


def check_config():
    """Check if config.py can be loaded"""
    print("\nChecking config...", end=" ")

    try:
        from config import settings
        print("✓ Configuration loaded")

        # Check important settings
        if settings.agents_batch == 2:
            print("  ⚠️  TODO: Change AGENTS_BATCH to 5 before demo!")

        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False


def main():
    """Run all checks"""
    print("🦖 Diagnosaurus.ai Setup Validation")
    print("=" * 50)

    checks = [
        check_python_version,
        check_dependencies,
        check_directories,
        check_env_file,
        check_config,
        check_redis,
    ]

    results = [check() for check in checks]

    print("\n" + "=" * 50)

    if all(results):
        print("✅ All checks passed! Ready to run.")
        print("\nNext steps:")
        print("  1. Run: ./run.sh")
        print("  2. Visit: http://localhost:5000")
        print("  3. Before demo: Change AGENTS_BATCH to 5 in config.py")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
