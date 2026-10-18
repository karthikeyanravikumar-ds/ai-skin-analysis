"""Main orchestration service for educational skin explanations."""

import logging
from typing import Any

from ai.explanation.client import generate_structured_response
from ai.explanation.fallback import build_fallback
from ai.explanation.guardrails import validate_explanation


logger = logging.getLogger(__name__)


def explain_analysis(context: dict[str, Any]) -> dict[str, Any]:
    """Generate a validated explanation or return a deterministic fallback."""

    try:
        generated = generate_structured_response(context)
        validated = validate_explanation(generated, context)
        return validated

    except Exception as exc:
        # Log only the exception type; avoid logging credentials or user data.
        logger.warning(
            "Gemini explanation unavailable; using deterministic fallback. "
            "Error type: %s",
            type(exc).__name__,
        )

    fallback = build_fallback(context)
    return validate_explanation(fallback, context)
