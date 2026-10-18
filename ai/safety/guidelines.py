"""
Medical Safety Guidelines and Triage Rules for Symptom Questionnaire Analysis.

Educational and preliminary triage guidance only.
Does NOT diagnose, prescribe medication, or provide treatment plans.
"""

from typing import Dict, List, Any


# Standard recognized questionnaire fields
QUESTIONNAIRE_FIELDS = [
    "duration",
    "location",
    "spreading",
    "itching",
    "pain",
    "burning",
    "swelling",
    "bleeding",
    "discharge",
    "blisters",
    "fever",
    "sensitiveArea",
    "previousOccurrence",
    "newExposure"
]

# Urgent Red Flag Definitions
URGENT_RED_FLAGS: Dict[str, str] = {
    "fever": "Presence of fever or systemic illness accompanying skin symptoms warrants prompt medical evaluation.",
    "blisters": "Blisters, open sores, or skin erosions require urgent clinical examination to rule out acute conditions.",
    "sensitiveArea": "Involvement of sensitive anatomical areas (eyes, mouth, lips, genitals) requires urgent specialist evaluation.",
    "bleeding": "Active bleeding or skin breakdown requires urgent professional medical assessment."
}

# Moderate Attention Warning Definitions
ATTENTION_FLAGS: Dict[str, str] = {
    "spreading": "Rapidly spreading or expanding lesions warrant timely clinical evaluation.",
    "discharge": "Fluid, pus, or weeping discharge suggests possible secondary infection requiring medical review.",
    "pain": "Significant skin pain or tenderness may indicate inflammation or deeper tissue involvement.",
    "swelling": "Noticeable swelling or edema should be evaluated by a healthcare professional.",
    "burning": "Intense burning or stinging sensation may indicate acute contact dermatitis or neural irritation.",
    "newExposure": "Onset following new medications, topical products, or environmental exposures may indicate an allergic or adverse reaction."
}

# Standard Clinical Safety Recommendations
RECOMMENDATIONS: Dict[str, str] = {
    "urgent": (
        "Urgent medical attention is advised. Please consult an emergency department, "
        "urgent care center, or a qualified healthcare provider immediately for professional clinical assessment."
    ),
    "attention": (
        "Timely medical consultation is recommended. Please schedule an evaluation with a "
        "dermatologist or qualified healthcare provider soon to monitor symptom progression."
    ),
    "routine": (
        "Routine dermatological consultation is suggested. Consider scheduling an in-person "
        "appointment with a healthcare professional or board-certified dermatologist for a comprehensive skin evaluation."
    )
}

# Standard Disclaimer
SAFETY_DISCLAIMER = (
    "This symptom and safety evaluation provides preliminary educational guidance only. "
    "It is not a medical diagnosis, prescription, or treatment plan. Always consult a qualified "
    "healthcare professional for any skin condition."
)
