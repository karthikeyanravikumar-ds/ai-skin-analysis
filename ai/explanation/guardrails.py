"""Validation and safety guardrails for educational explanations."""

import re
from typing import Any

from ai.explanation.schemas import ExplanationResponse


ALLOWED_CLASSES = {
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts",
}

ALLOWED_NEXT_STEPS = {
    "CONSULT_DERMATOLOGIST",
    "GENTLE_SKINCARE",
    "MONITOR_CHANGES",
    "SEEK_URGENT_CARE",
    "FOLLOW_EXISTING_MEDICAL_ADVICE",
}

# These checks are intentionally conservative. They supplement, rather than
# replace, clinical review and deterministic application safety decisions.
UNSAFE_PATTERNS = [
    r"\byou definitely have\b",
    r"\byou certainly have\b",
    r"\bdiagnosed with\b",
    r"\bdefinite(?:ly)?\s+diagnos(?:is|ed)\b",
    r"\b(?:confirms?|proves?|guarantees?)\s+(?:that\s+)?(?:you have|this is)\b",
    r"\b(?:we\s+)?prescribe\b",
    r"\bprescriptions?\s+(?:for|of)\b",
    r"\bprescribing\s+\w+\b",
    r"\btake\s+\d+\s*(?:mg|mcg|g|ml|tablets?|capsules?|drops?)\b",
    r"\bapply\s+\d+\s*(?:mg|ml|g)\b",
    r"\bdosage of\s+\d+\b",
    r"\bgrad-cam (?:proves|confirms|establishes)\b",
    r"\bno need to (?:see|visit|consult) a (?:doctor|physician|dermatologist)\b",
    r"\breplaces? (?:a|the)?\s*(?:doctor|physician|dermatologist|medical professional)\b",
]


class GuardrailError(ValueError):
    """Raised when an explanation fails a safety or consistency check."""


def validate_explanation(
    raw_response: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Validate the response schema and consistency with the CNN context."""
    response = ExplanationResponse.model_validate(raw_response)
    result = response.model_dump(mode="json")

    prediction = context.get("prediction")
    if not isinstance(prediction, str) or prediction not in ALLOWED_CLASSES:
        raise GuardrailError("CNN prediction is missing or unsupported.")

    confidence = context.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence <= 100
    ):
        raise GuardrailError("CNN confidence must be between 0 and 100.")

    # Check the dedicated model-output explanation, not unrelated educational
    # text that may mention other conditions for comparison.
    output_text = result["model_output_meaning"].casefold()
    normalized_prediction = prediction.replace("_", " ").casefold()

    mentioned_classes = [
        label.replace("_", " ")
        for label in ALLOWED_CLASSES
        if label.replace("_", " ") in output_text
    ]
    if normalized_prediction not in mentioned_classes:
        raise GuardrailError(
            "Model-output explanation does not identify the supplied CNN prediction."
        )

    # Do not allow another supported class to be presented as the CNN result.
    for other_class in mentioned_classes:
        if other_class != normalized_prediction:
            raise GuardrailError(
                "Model-output explanation mentions another supported class."
            )

    confidence_text = f"{float(confidence):.2f}%"
    confidence_number = re.compile(
        r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%"
    )
    percentages = [
        float(match.group(1))
        for match in confidence_number.finditer(
            " ".join(
                [
                    result["summary"],
                    result["model_output_meaning"],
                    result["uncertainty_explanation"],
                ]
            )
        )
    ]
    for pct in percentages:
        if abs(pct - float(confidence)) > 0.02 and abs(pct - 80.0) > 0.02:
            raise GuardrailError(
                f"Explanation contains a confidence percentage ({pct}%) inconsistent with {confidence_text}."
            )

    for step in result["next_steps"]:
        if step["code"] not in ALLOWED_NEXT_STEPS:
            raise GuardrailError("An unapproved next-step code was returned.")

    all_text = " ".join(
        [
            result["summary"],
            result["model_output_meaning"],
            result["reported_symptoms_context"],
            result["visual_attention_explanation"],
            result["uncertainty_explanation"],
            *(point["title"] + " " + point["explanation"]
              for point in result["educational_points"]),
            *(step["explanation"] for step in result["next_steps"]),
            *result["limitations"],
        ]
    ).casefold()

    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, all_text, flags=re.IGNORECASE):
            raise GuardrailError("Explanation contains potentially unsafe medical wording.")

    if float(confidence) < 80:
        uncertainty = result["uncertainty_explanation"].casefold()
        if not any(
            phrase in uncertainty
            for phrase in ("lower confidence", "low confidence", "less certain")
        ):
            raise GuardrailError(
                "Predictions below 80% confidence must explicitly state lower confidence."
            )

    safety_decision = context.get("safety_decision") or {}
    if isinstance(safety_decision, dict) and (
        safety_decision.get("is_emergency") is True
        or str(safety_decision.get("safety_level", "")).lower() == "urgent"
    ):
        step_codes = {step["code"] for step in result["next_steps"]}
        if not (step_codes & {"SEEK_URGENT_CARE", "CONSULT_DERMATOLOGIST"}):
            raise GuardrailError(
                "Urgent safety decision requires an urgent next-step recommendation."
            )

    return result
