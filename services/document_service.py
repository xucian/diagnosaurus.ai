"""
Document processing service
Extracts text from uploaded medical documents (PDFs, images)
"""
import base64
import io
from typing import List, Optional
from pypdf import PdfReader
from loguru import logger


class DocumentService:
    """Service for extracting text from medical documents"""

    def extract_text_from_pdf(self, pdf_base64: str) -> str:
        """
        Extract text from base64-encoded PDF

        Args:
            pdf_base64: Base64 encoded PDF data

        Returns:
            Extracted text content
        """
        try:
            # Decode base64
            pdf_bytes = base64.b64decode(pdf_base64)
            pdf_file = io.BytesIO(pdf_bytes)

            # Extract text from all pages
            reader = PdfReader(pdf_file)
            text_parts = []

            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{text}")

            extracted = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(extracted)} characters from PDF ({len(reader.pages)} pages)")
            return extracted

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return ""

    def extract_text_from_documents(self, documents: List[str]) -> str:
        """
        Extract text from multiple base64-encoded documents

        Args:
            documents: List of base64 encoded documents (PDFs)

        Returns:
            Concatenated text from all documents
        """
        if not documents:
            return ""

        extracted_texts = []

        for idx, doc_base64 in enumerate(documents, 1):
            logger.info(f"Processing document {idx}/{len(documents)}")

            # For now, assume PDFs (could add image OCR later)
            text = self.extract_text_from_pdf(doc_base64)

            if text:
                extracted_texts.append(f"=== Document {idx} ===\n{text}")
            else:
                logger.warning(f"No text extracted from document {idx}")

        if not extracted_texts:
            logger.warning("No text extracted from any documents")
            return ""

        combined = "\n\n".join(extracted_texts)
        logger.info(f"Total extracted text: {len(combined)} characters from {len(documents)} documents")
        return combined


# Global instance
document_service = DocumentService()
