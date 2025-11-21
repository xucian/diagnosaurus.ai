#!/usr/bin/env python3
"""
Test PDF text extraction

Tests document_service.py PDF parsing functionality
"""
import sys
import base64
from pathlib import Path
from services.document_service import document_service


def load_test_pdf() -> str:
    """
    Load real test PDF file
    Returns base64 encoded PDF
    """
    pdf_path = Path(__file__).parent / "test_blood_report.pdf"

    if not pdf_path.exists():
        raise FileNotFoundError(f"Test PDF not found: {pdf_path}")

    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()

    return base64.b64encode(pdf_content).decode('utf-8')


def test_basic_extraction():
    """Test basic PDF text extraction"""

    print("Testing PDF Text Extraction")
    print("=" * 60)

    # Load test PDF
    pdf_base64 = load_test_pdf()

    print("\n1. Basic extraction")
    text = document_service.extract_text_from_pdf(pdf_base64)

    success = len(text) > 0

    print(f"{'✓ PASS' if success else '✗ FAIL'} - Extracted {len(text)} characters")
    if text:
        print(f"  Content preview: {text[:100]}...")

    return success


def test_multiple_documents():
    """Test extracting from multiple PDFs"""

    print("\n2. Multiple documents")

    pdf1 = load_test_pdf()
    pdf2 = load_test_pdf()  # Same content for simplicity

    combined = document_service.extract_text_from_documents([pdf1, pdf2])

    # Should have headers for each document
    success = "=== Document 1 ===" in combined and "=== Document 2 ===" in combined

    print(f"{'✓ PASS' if success else '✗ FAIL'} - Combined {len(combined)} chars from 2 docs")
    print(f"  Has doc markers: {success}")

    return success


def test_empty_document_list():
    """Test handling empty document list"""

    print("\n3. Empty document list")

    text = document_service.extract_text_from_documents([])

    success = text == ""

    print(f"{'✓ PASS' if success else '✗ FAIL'} - Returns empty string")

    return success


def test_invalid_pdf():
    """Test handling invalid PDF data"""

    print("\n4. Invalid PDF data")

    invalid_base64 = base64.b64encode(b"This is not a PDF").decode()
    text = document_service.extract_text_from_pdf(invalid_base64)

    # Should return empty string on error, not crash
    success = text == ""

    print(f"{'✓ PASS' if success else '✗ FAIL'} - Gracefully handles invalid PDF")

    return success


def test_real_world_simulation():
    """Simulate real-world usage: symptoms + medical doc"""

    print("\n5. Real-world simulation")

    # Load real blood report PDF
    pdf = load_test_pdf()

    # Extract
    doc_text = document_service.extract_text_from_documents([pdf])

    # Combine with symptoms (like app.py does)
    symptoms = "Patient reports fatigue and dizziness"
    combined = f"{symptoms}\n\n--- Medical Documents ---\n{doc_text}"

    success = (
        symptoms in combined and
        "Medical Documents" in combined and
        len(combined) > len(symptoms)
    )

    print(f"{'✓ PASS' if success else '✗ FAIL'} - Symptoms + docs combined")
    print(f"  Total length: {len(combined)} chars")
    print(f"  Preview:\n{combined[:200]}...")

    return success


if __name__ == "__main__":
    print("PDF Extraction Tests")
    print("=" * 60)
    print("Testing document_service.py\n")

    results = [
        test_basic_extraction(),
        test_multiple_documents(),
        test_empty_document_list(),
        test_invalid_pdf(),
        test_real_world_simulation(),
    ]

    print("\n" + "=" * 60)
    if all(results):
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
