"""Deterministic fallback for educational skin-image explanations."""

from typing import Any

from ai.explanation.schemas import ExplanationResponse


CONDITION_NAMES = {
    "acne_vulgaris": "Acne vulgaris",
    "impetigo": "Impetigo",
    "molluscum_contagiosum": "Molluscum contagiosum",
    "psoriasis": "Psoriasis",
    "urticaria": "Urticaria (hives)",
    "vitiligo": "Vitiligo",
    "warts": "Warts",
}

GENERAL_INFORMATION = {
    "acne_vulgaris": (
        "Acne is a common skin condition involving hair follicles and oil glands."
    ),
    "impetigo": (
        "Impetigo is a contagious bacterial skin infection. A healthcare professional "
        "can assess suspected cases and advise on appropriate care."
    ),
    "molluscum_contagiosum": (
        "Molluscum contagiosum is a viral skin infection that can cause small, raised "
        "bumps. A clinician can help distinguish it from other skin conditions."
    ),
    "psoriasis": (
        "Psoriasis is a long-term inflammatory skin condition that may cause "
        "well-defined, scaly patches."
    ),
    "urticaria": (
        "Urticaria, also called hives, can cause raised, itchy skin welts. "
        "A clinician can help assess possible causes."
    ),
    "vitiligo": (
        "Vitiligo is a condition in which areas of skin lose pigment, producing "
        "lighter patches."
    ),
    "warts": (
        "Warts are growths commonly associated with certain types of human "
        "papillomavirus. Other skin growths can look similar."
    ),
}

COMMON_CHARACTERISTICS = {
    "acne_vulgaris": "Common characteristics can include blackheads, whiteheads, and inflamed bumps.",
    "impetigo": "Common characteristics can include sores, blisters, or crusted areas.",
    "molluscum_contagiosum": "Common characteristics can include small, firm, dome-shaped bumps, sometimes with a central indentation.",
    "psoriasis": "Common characteristics can include sharply defined, scaly patches.",
    "urticaria": "Common characteristics can include raised, itchy welts that may change location or appearance.",
    "vitiligo": "Common characteristics can include lighter patches of skin with reduced pigment.",
    "warts": "Common characteristics can include small, rough or raised skin growths.",
}


def build_fallback(context: dict[str, Any]) -> dict[str, Any]:
    """Create a predictable, schema-valid explanation without calling Gemini."""
    prediction = context.get("prediction")
    if prediction not in CONDITION_NAMES:
        raise ValueError("Unsupported or missing CNN prediction.")

    confidence = context.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence <= 100
    ):
        raise ValueError("CNN confidence must be between 0 and 100.")

    condition = CONDITION_NAMES[prediction]
    confidence_text = f"{float(confidence):.2f}%"

    if confidence < 80:
        uncertainty = (
            f"The CNN confidence is {confidence_text}, which is lower confidence "
            "under this application's 80% threshold. Image classification can "
            "make mistakes, and this result is not a medical diagnosis."
        )
    else:
        uncertainty = (
            f"The CNN confidence is {confidence_text}. A high confidence score "
            "does not establish medical certainty, and image classification can "
            "make mistakes."
        )

    symptoms = context.get("reported_symptoms")
    if isinstance(symptoms, list) and symptoms:
        symptoms_text = (
            "The supplied reported symptoms are: "
            + ", ".join(str(item) for item in symptoms[:10])
            + ". These reports are context only and do not confirm a condition."
        )
    elif isinstance(symptoms, dict) and symptoms:
        symptom_items = [f"{k}: {v}" for k, v in symptoms.items() if v is not None and str(v).strip()]
        if symptom_items:
            symptoms_text = (
                "The supplied reported symptoms are: "
                + ", ".join(symptom_items[:10])
                + ". These reports are context only and do not confirm a condition."
            )
        else:
            symptoms_text = (
                "No reported symptoms were supplied. The application cannot infer "
                "symptoms from the image."
            )
    else:
        symptoms_text = (
            "No reported symptoms were supplied. The application cannot infer "
            "symptoms from the image."
        )

    gradcam_available = context.get("gradcam_available") is True
    if gradcam_available:
        visual_text = (
            "Grad-CAM highlights image regions that influenced the CNN's "
            "prediction. These regions do not confirm medical findings or prove "
            "that a specific visual characteristic is present."
        )
    else:
        visual_text = (
            "A Grad-CAM visual explanation was not available for this result. "
            "No image regions can be described as highlighted by Grad-CAM."
        )

    result = ExplanationResponse(
        schema_version="1.0",
        summary=(
            f"The CNN predicted {condition} with a confidence score of "
            f"{confidence_text}. This is an educational model result, not a diagnosis."
        ),
        model_output_meaning=(
            f"The primary image classifier returned {prediction} "
            f"({condition}) with a confidence score of {confidence_text}. "
            "This explanation preserves that model output; it does not independently "
            "confirm the condition."
        ),
        reported_symptoms_context=symptoms_text,
        visual_attention_explanation=visual_text,
        uncertainty_explanation=uncertainty,
        educational_points=[
            {
                "title": "General information",
                "explanation": GENERAL_INFORMATION[prediction],
            },
            {
                "title": "Common characteristics",
                "explanation": COMMON_CHARACTERISTICS[prediction]
                + " These are general educational examples, not confirmed findings "
                "from the supplied image.",
            },
        ],
        next_steps=(
            [
                {
                    "code": "SEEK_URGENT_CARE",
                    "explanation": (
                        "Based on the reported symptoms and assessment, seek prompt or "
                        "urgent medical evaluation from a qualified healthcare provider."
                    ),
                },
                {
                    "code": "FOLLOW_EXISTING_MEDICAL_ADVICE",
                    "explanation": (
                        "If you are already receiving medical care for this condition, "
                        "continue following your healthcare provider's instructions."
                    ),
                },
            ]
            if (
                isinstance(context.get("safety_decision"), dict)
                and (
                    context["safety_decision"].get("is_emergency") is True
                    or str(context["safety_decision"].get("safety_level", "")).lower() == "urgent"
                )
            )
            else [
                {
                    "code": "CONSULT_DERMATOLOGIST",
                    "explanation": (
                        "Consider consulting a qualified dermatologist for an "
                        "individual assessment, particularly if the skin changes "
                        "persist, spread, worsen, or cause concern."
                    ),
                },
                {
                    "code": "GENTLE_SKINCARE",
                    "explanation": (
                        "Use gentle skin care and avoid picking, scraping, or irritating "
                        "the affected area. Do not change prescribed treatment based "
                        "on this automated result."
                    ),
                },
            ]
        ),
        limitations=[
            "This application provides educational guidance, not a medical diagnosis.",
            "An image classifier can misclassify skin conditions.",
            "A confidence score is not the probability of a confirmed diagnosis.",
            "Grad-CAM highlights model-influential regions, not verified medical features.",
            "A qualified healthcare professional can assess the skin in context.",
        ],
        content_ids=[
            f"condition.{prediction}",
            "safety.educational_only",
            "safety.image_uncertainty",
        ],
        guardrail_flags=["deterministic_fallback", "not_a_medical_diagnosis"],
    )

    return result.model_dump(mode="json")
