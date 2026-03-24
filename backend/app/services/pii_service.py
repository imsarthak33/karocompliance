"""
Enterprise DLP — PII Redaction Service for DPDP Act Compliance.

Masks sensitive Indian PII (PAN, Aadhaar, Bank Account, Phone) with reversible tokens
before sending text to third-party LLMs, then unmasks extracted JSON afterward.
"""
import re
import logging
from typing import Dict, Tuple

import sentry_sdk  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Indian PII Regex Patterns
# ---------------------------------------------------------------------------
# PAN Card: 5 uppercase letters, 4 digits, 1 uppercase letter
_PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

# Aadhaar: 12 digits, optionally separated by spaces (first digit 2-9)
_AADHAAR_RE = re.compile(r"\b[2-9][0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b")

# Indian Phone: optional +91 or 91 prefix followed by 10-digit mobile number
_PHONE_RE = re.compile(r"(?<!\d)(?:\+91[\s-]?|91[\s-]?)?[6-9][0-9]{9}(?!\d)")

# Bank Account: 9-18 digit sequences (most Indian bank accounts)
_BANK_ACCOUNT_RE = re.compile(r"\b[0-9]{9,18}\b")

# IFSC Code: 4 letters, 0, 7 alphanumeric characters
_IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")

# Ordered from most specific to least specific to prevent overlapping matches
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("PAN", _PAN_RE),
    ("IFSC", _IFSC_RE),
    ("AADHAAR", _AADHAAR_RE),
    ("PHONE", _PHONE_RE),
    ("BANK_ACCT", _BANK_ACCOUNT_RE),
]


class PIIRedactor:
    """Mask and unmask PII in text using deterministic token replacement."""

    @staticmethod
    def mask(text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace every PII occurrence with a bracketed token.

        Returns:
            (masked_text, token_map) where token_map maps "[PAN_1]" -> original value.
        """
        token_map: Dict[str, str] = {}
        counters: Dict[str, int] = {}
        masked_positions: list[tuple[int, int]] = []  # track already-masked ranges

        for pii_type, pattern in _PII_PATTERNS:
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()

                # Skip if this range overlaps with an already-masked region
                if any(ms <= start < me or ms < end <= me for ms, me in masked_positions):
                    continue

                original_value = match.group()
                counter = counters.get(pii_type, 0) + 1
                counters[pii_type] = counter
                token = f"[{pii_type}_{counter}]"
                token_map[token] = original_value
                masked_positions.append((start, end))

        # Replace from end to start to preserve positions
        for pii_type, pattern in _PII_PATTERNS:
            matches = list(pattern.finditer(text))
            for match in reversed(matches):
                start, end = match.start(), match.end()
                original_value = match.group()
                # Find the corresponding token
                matching_token = next(
                    (tok for tok, val in token_map.items() if val == original_value),
                    None,
                )
                if matching_token:
                    text = text[:start] + matching_token + text[end:]

        logger.info(
            "PII Redactor: masked %d items (%s)",
            len(token_map),
            ", ".join(f"{k.split('_')[0].strip('[')}: {v}" for k, v in counters.items()) if counters else "none",
        )
        return text, token_map

    @staticmethod
    def unmask(text: str, token_map: Dict[str, str]) -> str:
        """Restore original PII values from tokens in extracted text/JSON."""
        for token, original_value in token_map.items():
            text = text.replace(token, original_value)
        return text

    @staticmethod
    def unmask_dict(data: dict, token_map: Dict[str, str]) -> dict:
        """Recursively unmask all string values in a dictionary."""
        if not token_map:
            return data

        def _unmask_value(value):  # type: ignore
            if isinstance(value, str):
                for token, original in token_map.items():
                    value = value.replace(token, original)
                return value
            elif isinstance(value, dict):
                return {k: _unmask_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_unmask_value(item) for item in value]
            return value

        return _unmask_value(data)
