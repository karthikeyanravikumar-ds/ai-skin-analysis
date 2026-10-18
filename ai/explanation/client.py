"""Gemini API client for structured educational explanations."""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from ai.explanation.prompt import SYSTEM_PROMPT
from ai.explanation.schemas import ExplanationResponse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _build_gemini_schema() -> dict[str, Any]:
    """Build a Gemini-compatible JSON schema from the Pydantic model."""
    schema = ExplanationResponse.model_json_schema()

    def sanitize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: sanitize(child)
                for key, child in value.items()
                if key not in {"additionalProperties", "additional_properties"}
            }
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        return value

    return sanitize(schema)


def generate_structured_response(context: dict[str, Any]) -> dict[str, Any]:
    """Generate an educational explanation without changing the CNN result."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    model_name = os.getenv("GEMINI_EXPLANATION_MODEL", "gemini-3.8-flash")
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=30000),
    )

    request = {
        "system_instructions": SYSTEM_PROMPT,
        "analysis_context": context,
        "output_requirements": (
            "Return only a JSON object that strictly matches the provided schema. "
            "Preserve the supplied CNN prediction and confidence."
        ),
    }

    response = client.models.generate_content(
        model=model_name,
        contents=json.dumps(request, ensure_ascii=False),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_build_gemini_schema(),
            temperature=0.2,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    parsed = json.loads(response.text)

    # Validate the response locally, even when Gemini enforces a response schema.
    validated = ExplanationResponse.model_validate(parsed)
    return validated.model_dump(mode="json")
