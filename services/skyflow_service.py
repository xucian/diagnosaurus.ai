"""
Skyflow API integration for data sanitization
Tokenizes sensitive medical information (PII/PHI) in text
Uses Skyflow 2.0 SDK API
"""
from typing import Dict, Any, List, Optional
import base64
import re
from loguru import logger
from config import settings

# Optional Skyflow SDK v2.x
try:
    from skyflow import Skyflow, Env, LogLevel
    from skyflow.vault.data import InsertRequest
    from skyflow.vault.tokens import DetokenizeRequest
    from skyflow.vault.detect import DeidentifyTextRequest
    from skyflow.utils.enums.detect_entities import DetectEntities
    SKYFLOW_SDK_AVAILABLE = True
except ImportError:
    SKYFLOW_SDK_AVAILABLE = False
    logger.warning("Skyflow SDK not available - using regex fallback only")


class SkyflowService:
    """Skyflow data sanitization service"""

    def __init__(self):
        """Initialize Skyflow client using v2.x SDK"""
        # Check if SDK is available
        if not SKYFLOW_SDK_AVAILABLE:
            logger.info("Skyflow SDK not available, using regex fallback")
            self.client = None
            self.vault_id = None
            return

        # Check if Skyflow is configured
        if not all([settings.skyflow_vault_id, settings.skyflow_api_key]):
            logger.info("Skyflow not configured, using regex fallback for PII redaction")
            self.client = None
            self.vault_id = None
            return

        try:
            # Determine environment and cluster_id from vault URL
            # Production format: https://<cluster_id>.vault.skyflowapis.com
            # Preview format: https://<account_id>.vault.skyflowapis-preview.com
            env = Env.PROD
            cluster_id = None

            if settings.skyflow_vault_url:
                url_lower = settings.skyflow_vault_url.lower()
                if 'skyflowapis-preview' in url_lower:
                    env = Env.DEV  # Preview environment
                elif 'sandbox' in url_lower:
                    env = Env.SANDBOX

                # Extract cluster_id from URL
                # Production: https://<cluster_id>.vault.skyflowapis.com
                # Preview: https://<cluster_id>.vault.skyflowapis-preview.com
                parts = settings.skyflow_vault_url.replace('https://', '').split('.')
                if len(parts) >= 2:
                    cluster_id = parts[0]  # First part is always the cluster/account ID

            # Use bearer token format (JWT token from service account)
            credentials = {'token': settings.skyflow_api_key}

            vault_config = {
                'vault_id': settings.skyflow_vault_id,
                'credentials': credentials,
                'env': env
            }

            # Add cluster_id (required by Skyflow SDK)
            if cluster_id:
                vault_config['cluster_id'] = cluster_id
            else:
                raise ValueError("Could not extract cluster_id from vault URL")

            self.client = (
                Skyflow.builder()
                .add_vault_config(vault_config)
                .set_log_level(LogLevel.ERROR)
                .build()
            )

            self.vault_id = settings.skyflow_vault_id
            logger.info(f"Skyflow service initialized successfully (v2.0 SDK, env={env.value if hasattr(env, 'value') else env})")

        except Exception as e:
            logger.error(f"Failed to initialize Skyflow: {e}")
            self.client = None
            self.vault_id = None

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
            # Use Skyflow's deidentify_text for PII detection
            deidentify_request = DeidentifyTextRequest(
                text=text,
                entities=[DetectEntities.ALL]  # Detect all PII types
            )

            response = self.client.detect(self.vault_id).deidentify_text(deidentify_request)

            # Extract redacted text from response
            if hasattr(response, 'redacted_text'):
                logger.info("Skyflow text deidentification successful")
                return response.redacted_text
            elif isinstance(response, dict) and 'redacted_text' in response:
                logger.info("Skyflow text deidentification successful")
                return response['redacted_text']
            else:
                logger.warning("Skyflow response format unexpected, using regex fallback")
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
            r'\b\d{3}[-.\s]\d{4}\b',  # XXX-XXXX (shorter format)
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
        Sanitize sensitive data through Skyflow tokenization (v2 SDK)

        Args:
            data: Dictionary containing sensitive fields

        Returns:
            Dictionary with sensitive fields tokenized
        """
        if not self.client or not self.vault_id:
            logger.warning("Skyflow not initialized, returning unsanitized data")
            return data

        try:
            # Identify sensitive fields (PII/PHI)
            sensitive_fields = self._identify_sensitive_fields(data)

            if not sensitive_fields:
                return data

            # Prepare data for insertion with v2 API
            insert_data = [{
                key: value
                for key, value in data.items()
                if key in sensitive_fields
            }]

            # Create InsertRequest with v2 SDK
            insert_request = InsertRequest(
                table="medical_data",
                values=insert_data,
                return_tokens=True,
                continue_on_error=True
            )

            # Insert into vault
            response = self.client.vault(self.vault_id).insert(insert_request)

            # Replace sensitive fields with tokens
            tokenized_data = data.copy()
            if hasattr(response, 'records') and response.records:
                tokens = getattr(response.records[0], 'tokens', {})
                for field, token in tokens.items():
                    tokenized_data[field] = token
            elif isinstance(response, dict) and 'records' in response:
                tokens = response['records'][0].get('tokens', {})
                for field, token in tokens.items():
                    tokenized_data[field] = token

            logger.info(f"Sanitized {len(sensitive_fields)} sensitive fields")
            return tokenized_data

        except Exception as e:
            logger.error(f"Skyflow sanitization failed: {e}")
            return self._redact_sensitive_fields(data)

    def detokenize_data(self, tokenized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detokenize Skyflow tokens back to original values (v2 SDK)

        Args:
            tokenized_data: Dictionary containing Skyflow tokens

        Returns:
            Dictionary with original values restored
        """
        if not self.client or not self.vault_id:
            return tokenized_data

        try:
            # Identify token fields
            token_fields = [k for k, v in tokenized_data.items() if self._is_token(v)]

            if not token_fields:
                return tokenized_data

            # Create detokenize request with v2 SDK
            tokens_list = [tokenized_data[field] for field in token_fields]

            detokenize_request = DetokenizeRequest(
                tokens=tokens_list,
                continue_on_error=True
            )

            response = self.client.vault(self.vault_id).detokenize(detokenize_request)

            # Restore original values
            restored_data = tokenized_data.copy()
            if hasattr(response, 'records') and response.records:
                for i, field in enumerate(token_fields):
                    if i < len(response.records):
                        restored_data[field] = getattr(response.records[i], 'value', tokenized_data[field])
            elif isinstance(response, dict) and 'records' in response:
                for i, field in enumerate(token_fields):
                    if i < len(response['records']):
                        restored_data[field] = response['records'][i].get('value', tokenized_data[field])

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
