"""
Skyflow API integration for data sanitization
Tokenizes sensitive medical information (PII/PHI) in text
"""
from typing import Dict, Any, List, Optional
import base64
import re
from skyflow.vault import Client, Configuration, InsertOptions
from skyflow.service_account import generate_bearer_token
from loguru import logger
from config import settings


class SkyflowService:
    """Skyflow data sanitization service"""

    def __init__(self):
        """Initialize Skyflow client"""
        # Check if Skyflow is configured
        if not all([settings.skyflow_vault_id, settings.skyflow_vault_url, settings.skyflow_api_key]):
            logger.info("Skyflow not configured, using regex fallback for PII redaction")
            self.client = None
            return

        try:
            config = Configuration(
                vault_id=settings.skyflow_vault_id,
                vault_url=settings.skyflow_vault_url,
                token_provider=self._get_token,
            )
            self.client = Client(config)
            logger.info("Skyflow service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Skyflow: {e}")
            self.client = None

    def _get_token(self) -> str:
        """Generate Skyflow bearer token"""
        try:
            return generate_bearer_token(settings.skyflow_api_key)
        except Exception as e:
            logger.error(f"Failed to generate Skyflow token: {e}")
            return ""

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize PII/PHI in text content

        Args:
            text: Raw text containing potential PII

        Returns:
            Text with PII redacted/tokenized
        """
        if not text:
            return text

        if self.client:
            # Use Skyflow API for PII detection
            return self._skyflow_sanitize_text(text)
        else:
            # Fallback to regex-based redaction
            return self._regex_sanitize_text(text)

    def _skyflow_sanitize_text(self, text: str) -> str:
        """Use Skyflow API for text-level PII detection"""
        try:
            # Skyflow's text redaction API (simplified - actual API may differ)
            # For now, fall back to regex if Skyflow text API is complex
            logger.warning("Skyflow text API not fully implemented, using regex fallback")
            return self._regex_sanitize_text(text)
        except Exception as e:
            logger.error(f"Skyflow text sanitization failed: {e}")
            return self._regex_sanitize_text(text)

    def _regex_sanitize_text(self, text: str) -> str:
        """
        Regex-based PII redaction (fallback)
        Detects and redacts common PII patterns
        """
        sanitized = text
        redaction_count = 0

        # SSN patterns (XXX-XX-XXXX)
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        matches = re.findall(ssn_pattern, sanitized)
        if matches:
            sanitized = re.sub(ssn_pattern, '[SSN_REDACTED]', sanitized)
            redaction_count += len(matches)

        # Date of birth patterns (various formats)
        dob_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY or M/D/YYYY
        ]
        for pattern in dob_patterns:
            matches = re.findall(pattern, sanitized)
            if matches:
                sanitized = re.sub(pattern, '[DOB_REDACTED]', sanitized)
                redaction_count += len(matches)

        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, sanitized)
        if matches:
            sanitized = re.sub(email_pattern, '[EMAIL_REDACTED]', sanitized)
            redaction_count += len(matches)

        # Phone numbers (various formats)
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # XXX-XXX-XXXX
            r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',  # (XXX) XXX-XXXX
        ]
        for pattern in phone_patterns:
            matches = re.findall(pattern, sanitized)
            if matches:
                sanitized = re.sub(pattern, '[PHONE_REDACTED]', sanitized)
                redaction_count += len(matches)

        # Medical record numbers (MRN: followed by digits)
        mrn_pattern = r'\bMRN[:\s]*\d{5,}\b'
        matches = re.findall(mrn_pattern, sanitized, re.IGNORECASE)
        if matches:
            sanitized = re.sub(mrn_pattern, '[MRN_REDACTED]', sanitized, flags=re.IGNORECASE)
            redaction_count += len(matches)

        if redaction_count > 0:
            logger.info(f"Redacted {redaction_count} PII patterns using regex")

        return sanitized

    def sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize sensitive data through Skyflow tokenization

        Args:
            data: Dictionary containing sensitive fields

        Returns:
            Dictionary with sensitive fields tokenized
        """
        if not self.client:
            logger.warning("Skyflow not initialized, returning unsanitized data")
            return data

        try:
            # Identify sensitive fields (PII/PHI)
            sensitive_fields = self._identify_sensitive_fields(data)

            if not sensitive_fields:
                return data

            # Prepare records for tokenization
            records = {
                "records": [
                    {
                        "fields": {
                            key: value
                            for key, value in data.items()
                            if key in sensitive_fields
                        }
                    }
                ]
            }

            # Insert into Skyflow vault (tokenization)
            options = InsertOptions(tokens=True)
            response = self.client.insert(
                records=records,
                table="medical_data",
                options=options,
            )

            # Replace sensitive fields with tokens
            tokenized_data = data.copy()
            if response and "records" in response:
                tokens = response["records"][0].get("tokens", {})
                for field, token in tokens.items():
                    tokenized_data[field] = token

            logger.info(f"Sanitized {len(sensitive_fields)} sensitive fields")
            return tokenized_data

        except Exception as e:
            logger.error(f"Skyflow sanitization failed: {e}")
            # Redact sensitive fields as fallback
            return self._redact_sensitive_fields(data)

    def detokenize_data(self, tokenized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detokenize Skyflow tokens back to original values

        Args:
            tokenized_data: Dictionary containing Skyflow tokens

        Returns:
            Dictionary with original values restored
        """
        if not self.client:
            return tokenized_data

        try:
            # Identify token fields
            token_fields = [k for k, v in tokenized_data.items() if self._is_token(v)]

            if not token_fields:
                return tokenized_data

            # Detokenize request
            detokenize_request = {
                "detokenizationParameters": [
                    {"token": tokenized_data[field]}
                    for field in token_fields
                ]
            }

            response = self.client.detokenize(detokenize_request)

            # Restore original values
            restored_data = tokenized_data.copy()
            if response and "records" in response:
                for i, field in enumerate(token_fields):
                    restored_data[field] = response["records"][i].get("value")

            return restored_data

        except Exception as e:
            logger.error(f"Skyflow detokenization failed: {e}")
            return tokenized_data

    def sanitize_document(self, document_base64: str, filename: str) -> Dict[str, Any]:
        """
        Sanitize uploaded medical document

        Args:
            document_base64: Base64 encoded document
            filename: Original filename

        Returns:
            Dictionary with file token and metadata
        """
        if not self.client:
            logger.warning("Skyflow not initialized, skipping document sanitization")
            return {"token": "UNSANITIZED", "filename": filename}

        try:
            # Store file in Skyflow file vault
            file_data = {
                "file": document_base64,
                "filename": filename,
            }

            response = self.client.insert_file(
                table="medical_documents",
                file=file_data,
            )

            logger.info(f"Sanitized document: {filename}")
            return {
                "token": response.get("skyflow_id"),
                "filename": filename,
            }

        except Exception as e:
            logger.error(f"Document sanitization failed: {e}")
            return {"token": "SANITIZATION_FAILED", "filename": filename}

    def _identify_sensitive_fields(self, data: Dict[str, Any]) -> List[str]:
        """Identify fields containing PII/PHI"""
        sensitive_patterns = [
            "name", "ssn", "dob", "birth", "phone", "email",
            "address", "insurance", "medical_record", "patient_id",
        ]
        return [
            key for key in data.keys()
            if any(pattern in key.lower() for pattern in sensitive_patterns)
        ]

    def _redact_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: Redact sensitive fields if Skyflow fails"""
        redacted = data.copy()
        sensitive = self._identify_sensitive_fields(data)
        for field in sensitive:
            redacted[field] = "[REDACTED]"
        return redacted

    def _is_token(self, value: Any) -> bool:
        """Check if value is a Skyflow token"""
        if not isinstance(value, str):
            return False
        # Skyflow tokens typically start with specific prefix
        return value.startswith("tok_") or len(value) == 32


# Global instance
skyflow_service = SkyflowService()
