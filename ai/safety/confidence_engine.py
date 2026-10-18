"""
Confidence & Uncertainty Interpretation Engine for AI Skin Analysis.

Interprets the raw PyTorch CNN model confidence scores conservatively without
modifying, scaling, or calibrating the mathematical confidence.

Strict Medical & Technical Guardrails:
- PRESERVES the exact original CNN confidence.
- PRESERVES the original CNN prediction.
- NEVER claims model confidence equals clinical probability of disease.
- NEVER provides definitive medical diagnosis or treatment advice.
- Translates model confidence into conservative educational guidance and uncertainty levels.
- Factors in technical image quality contextually to advise caution.
"""

import math
from typing import Dict, Any, Optional, Union


# ============================================================
# CONFIGURABLE THRESHOLDS
# ============================================================

HIGH_CONFIDENCE_THRESHOLD: float = 0.80
MODERATE_CONFIDENCE_THRESHOLD: float = 0.60


# ============================================================
# EDUCATIONAL MESSAGING TEMPLATES
# ============================================================

MESSAGES: Dict[str, str] = {
    "high": (
        "The model produced a relatively high-confidence image classification. "
        "This is still a preliminary AI prediction and should not be treated as a confirmed medical diagnosis."
    ),
    "moderate": (
        "The model produced a moderate-confidence image classification. "
        "The result should be interpreted cautiously and does not confirm a medical diagnosis."
    ),
    "low": (
        "The model produced a low-confidence image classification. The image may not contain enough "
        "information for a reliable model prediction. Consider using a clearer image and/or seeking professional evaluation."
    )
}

RECOMMENDED_NEXT_STEPS: Dict[str, str] = {
    "high": (
        "Consider scheduling a routine consultation with a healthcare professional or dermatologist for in-person evaluation."
    ),
    "moderate": (
        "Seek in-person clinical assessment by a healthcare professional or board-certified dermatologist for a comprehensive evaluation."
    ),
    "low": (
        "Retake a clear, well-lit, in-focus photograph of the skin lesion or consult a qualified healthcare provider directly."
    )
}


def assess_confidence(
    confidence: Any,
    image_quality: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Interpret model confidence score and determine uncertainty status.

    Args:
        confidence: Raw probability score [0.0 .. 1.0] from CNN output.
        image_quality: Optional dictionary returned by image_quality assessment.

    Returns:
        Structured dictionary containing:
          - confidence: Exact original unrounded float
          - confidence_percent: Display percentage rounded to 2 decimal places
          - level: 'high' | 'moderate' | 'low'
          - uncertainty_status: 'high_confidence' | 'moderate_uncertainty' | 'low_confidence'
          - requires_caution: bool
          - message: Conservative educational message
          - recommended_next_step: Actionable non-diagnostic guidance
          - quality_impact: Optional explanation if technical quality concerns exist
    """
    # --------------------------------------------------------
    # 1. VALIDATE AND NORMALIZE INPUT CONFIDENCE
    # --------------------------------------------------------
    is_valid_numeric = True
    clean_confidence = 0.0

    if confidence is None or isinstance(confidence, bool):
        is_valid_numeric = False
    elif isinstance(confidence, (int, float)):
        clean_confidence = float(confidence)
        if not math.isfinite(clean_confidence) or clean_confidence < 0.0 or clean_confidence > 1.0:
            is_valid_numeric = False
    else:
        try:
            clean_confidence = float(confidence)
            if not math.isfinite(clean_confidence) or clean_confidence < 0.0 or clean_confidence > 1.0:
                is_valid_numeric = False
        except (ValueError, TypeError):
            is_valid_numeric = False

    if not is_valid_numeric:
        return {
            "confidence": 0.0,
            "confidence_percent": 0.0,
            "level": "low",
            "uncertainty_status": "low_confidence",
            "requires_caution": True,
            "message": (
                "An invalid confidence value was encountered. The prediction output "
                "cannot be reliably evaluated and must be treated with high uncertainty."
            ),
            "recommended_next_step": (
                "Please repeat the image analysis or consult a healthcare professional in person."
            ),
            "quality_impact": "Invalid model output."
        }

    # --------------------------------------------------------
    # 2. DETERMINE LEVEL AND UNCERTAINTY STATUS
    # --------------------------------------------------------
    if clean_confidence >= HIGH_CONFIDENCE_THRESHOLD:
        level = "high"
        uncertainty_status = "high_confidence"
        requires_caution = False
    elif clean_confidence >= MODERATE_CONFIDENCE_THRESHOLD:
        level = "moderate"
        uncertainty_status = "moderate_uncertainty"
        requires_caution = True
    else:
        level = "low"
        uncertainty_status = "low_confidence"
        requires_caution = True

    message = MESSAGES[level]
    recommended_next_step = RECOMMENDED_NEXT_STEPS[level]
    quality_impact = None

    # --------------------------------------------------------
    # 3. CONTEXTUAL IMAGE QUALITY INTERACTION
    # --------------------------------------------------------
    if isinstance(image_quality, dict):
        q_status = image_quality.get("status")
        if q_status == "poor":
            requires_caution = True
            quality_impact = "The uploaded image has technical quality limitations that may compromise classification reliability."
            if level == "high":
                message = (
                    f"{MESSAGES[level]} However, technical image quality limitations were detected. "
                    f"Interpret the classification with additional caution."
                )
        elif q_status == "warning":
            requires_caution = True
            quality_impact = "Minor technical image quality warnings were detected."
            if level == "high":
                message = (
                    f"{MESSAGES[level]} Minor technical image warnings were detected; "
                    f"interpret with appropriate caution."
                )

    # --------------------------------------------------------
    # 4. PREPARE STRUCTURED RESULT
    # --------------------------------------------------------
    return {
        "confidence": clean_confidence,
        "confidence_percent": round(clean_confidence * 100, 2),
        "level": level,
        "uncertainty_status": uncertainty_status,
        "requires_caution": requires_caution,
        "message": message,
        "recommended_next_step": recommended_next_step,
        "quality_impact": quality_impact
    }
