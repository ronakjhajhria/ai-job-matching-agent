"""Phase 13: Input Guardrails — validation before any LLM call."""

import re
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Simple patterns for prompt injection and PII detection
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(the\s+)?system\s+prompt",
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if|a|an)\s+",
    r"jailbreak",
    r"dan\s+mode",
    r"pretend\s+you\s+are",
]

PII_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[- ]?){3}\d{4}\b",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
}


class GuardrailResult(BaseModel):
    is_safe: bool
    reasons: list[str]
    sanitized_text: str


def check_input(text: str) -> GuardrailResult:
    """
    Validate and lightly sanitize user input before passing it to an LLM.
    
    Limitations (documented per project rules):
    - Pattern-based injection detection is not foolproof.
    - A sophisticated adversary can evade regex-based checks.
    - This is a best-effort guardrail, not a complete security solution.
    """
    reasons = []
    sanitized = text

    # 1. Length check
    if len(text) > 20_000:
        reasons.append("Input exceeds maximum allowed length of 20,000 characters.")
        return GuardrailResult(is_safe=False, reasons=reasons, sanitized_text=text)

    # 2. Prompt injection detection
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            reasons.append(f"Possible prompt injection detected (pattern: '{pattern}')")
            logger.warning(f"Prompt injection pattern matched: {pattern}")

    # 3. PII redaction (redact, don't block)
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, text):
            sanitized = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", sanitized)
            reasons.append(f"PII redacted: {pii_type}")
            logger.info(f"PII redacted: {pii_type}")

    is_safe = not any("injection" in r.lower() for r in reasons)
    return GuardrailResult(is_safe=is_safe, reasons=reasons, sanitized_text=sanitized)
