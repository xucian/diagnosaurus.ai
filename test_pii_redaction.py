#!/usr/bin/env python3
"""
Test PII/PHI redaction functionality

Tests regex-based redaction (always works, no API keys needed)
"""
import sys
from services.skyflow_service import skyflow_service


def test_pii_patterns():
    """Test various PII pattern detection"""

    test_cases = [
        {
            "name": "SSN",
            "input": "Patient SSN is 123-45-6789",
            "expected": "[SSN_REDACTED]"
        },
        {
            "name": "Email",
            "input": "Contact: john.smith@example.com",
            "expected": "[EMAIL_REDACTED]"
        },
        {
            "name": "Phone",
            "input": "Call me at 555-123-4567",
            "expected": "[PHONE_REDACTED]"
        },
        {
            "name": "DOB (YYYY-MM-DD)",
            "input": "Born on 1985-03-15",
            "expected": "[DOB_REDACTED]"
        },
        {
            "name": "DOB (MM/DD/YYYY)",
            "input": "DOB: 03/15/1985",
            "expected": "[DOB_REDACTED]"
        },
        {
            "name": "MRN",
            "input": "MRN: 987654",
            "expected": "[MRN_REDACTED]"
        },
        {
            "name": "Multiple PII",
            "input": "Patient: john@test.com, SSN: 123-45-6789, Phone: 555-1234",
            "expected": ["[EMAIL_REDACTED]", "[SSN_REDACTED]", "[PHONE_REDACTED]"]
        }
    ]

    print("Testing PII Redaction")
    print("=" * 60)

    passed = 0
    failed = 0

    for test in test_cases:
        sanitized = skyflow_service.sanitize_text(test["input"])

        if isinstance(test["expected"], list):
            # Check all patterns present
            success = all(pattern in sanitized for pattern in test["expected"])
        else:
            success = test["expected"] in sanitized

        status = "✓ PASS" if success else "✗ FAIL"

        print(f"\n{status} - {test['name']}")
        print(f"  Input:     {test['input']}")
        print(f"  Sanitized: {sanitized}")

        if success:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    return failed == 0


def test_no_false_positives():
    """Ensure normal text isn't over-redacted"""

    normal_text = "Patient reports fatigue and dizziness for 2 weeks. Age 35."
    sanitized = skyflow_service.sanitize_text(normal_text)

    # Should be unchanged (no PII patterns)
    success = sanitized == normal_text

    print(f"\n{'✓ PASS' if success else '✗ FAIL'} - No false positives")
    print(f"  Input:     {normal_text}")
    print(f"  Sanitized: {sanitized}")

    return success


def test_combined_text():
    """Test realistic combined symptoms + document text"""

    combined = """Patient symptoms: Persistent fatigue, pale skin, dizziness.

--- Medical Documents ---
Patient Name: John Smith
Email: patient@email.com
Phone: (555) 123-4567
DOB: 1985-03-15
MRN: 123456
SSN: 123-45-6789

Lab Results:
Hemoglobin: 8.2 g/dL (Low)
Iron: 30 μg/dL (Low)
"""

    sanitized = skyflow_service.sanitize_text(combined)

    # Check redactions present
    redactions = ["[EMAIL_REDACTED]", "[PHONE_REDACTED]", "[DOB_REDACTED]", "[SSN_REDACTED]", "[MRN_REDACTED]"]
    success = all(r in sanitized for r in redactions)

    # Check medical data preserved
    preserved = all(text in sanitized for text in ["Hemoglobin", "8.2 g/dL", "Iron", "30 μg/dL"])
    success = success and preserved

    print(f"\n{'✓ PASS' if success else '✗ FAIL'} - Combined text (symptoms + documents)")
    print(f"  Redactions found: {sum(1 for r in redactions if r in sanitized)}/{len(redactions)}")
    print(f"  Medical data preserved: {preserved}")
    print(f"\n  Sanitized preview:\n{sanitized[:300]}...")

    return success


if __name__ == "__main__":
    print("PII/PHI Redaction Tests")
    print("=" * 60)
    print("Testing regex fallback (no Skyflow API needed)\n")

    results = [
        test_pii_patterns(),
        test_no_false_positives(),
        test_combined_text(),
    ]

    print("\n" + "=" * 60)
    if all(results):
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
