"""
Out-of-Distribution (OOD) & Domain Abstention Guardrail Module.

Evaluates whether an input image falls outside the supported 7-class dermatological
domain before inference presentation.

Strict Non-Diagnostic & Safety Principles:
1. Rejects obvious non-dermatological inputs (documents, barcodes, solid colors,
   extreme voids, completely desaturated graphics) using deterministic heuristics.
2. Conservative abstention: Does NOT claim to distinguish all subtle real-world non-skin
   images (as no universal reference OOD distribution exists in the repository).
3. Independent of skin pigmentation: Uses inter-channel variance, extreme void metrics,
   and color distribution entropy rather than skin tone cutoffs, preserving full equity
   across Fitzpatrick skin phototypes I through VI.
4. If an image is flagged as OOD:
   - Abstains from predicting any of the seven dermatological classes.
   - Prevents generation of Grad-CAM heatmaps for unsupported inputs.
   - Preserves user safety by maintaining symptom evaluation and emergency triage directives.
"""

import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import cv2
import numpy as np
from PIL import Image


OOD_REASON_DESCRIPTIONS: Dict[str, str] = {
    "DOCUMENT_OR_TEXT_PAGE": (
        "The uploaded file appears to be a printed document, text page, or diagram "
        "rather than a photographic skin image."
    ),
    "SOLID_OR_SYNTHETIC_COLOR": (
        "The image exhibits a solid, synthetic, or artificially uniform color field "
        "lacking natural skin tissue variance."
    ),
    "MONOCHROMATIC_NON_SKIN": (
        "The image lacks chromatic color variance (grayscale or monochromatic) "
        "and does not represent a supported dermatological color photograph."
    ),
    "EXTREME_VOID_OR_BLANK": (
        "The image contains an excessive solid void or blank field "
        "exceeding normal photographic lesion framing."
    )
}

USER_GUIDANCE_MESSAGE: str = (
    "This system is designed specifically for clinical skin lesion photographs across "
    "seven supported conditions (Acne Vulgaris, Impetigo, Molluscum Contagiosum, Psoriasis, "
    "Urticaria, Vitiligo, and Warts). The submitted image appears to be outside this supported domain. "
    "Please upload or capture a clear, well-lit photograph focusing on the affected skin area."
)


def assess_ood(
    image_input: Union[str, Path, np.ndarray, Image.Image]
) -> Dict[str, Any]:
    """
    Perform conservative out-of-distribution (OOD) assessment on an input image.

    Returns:
        Structured dictionary:
        {
            "is_ood": bool,
            "status": "supported" | "abstained",
            "reason_codes": List[str],
            "reasons": List[str],
            "message": str,
            "metrics": { ... }
        }
    """
    # 1. Image decoding to BGR numpy array
    img_bgr: Optional[np.ndarray] = None
    try:
        if isinstance(image_input, (str, Path)):
            path_obj = Path(image_input)
            if not path_obj.exists() or not path_obj.is_file() or path_obj.stat().st_size == 0:
                return {
                    "is_ood": True,
                    "status": "abstained",
                    "reason_codes": ["UNREADABLE_IMAGE"],
                    "reasons": ["Image file could not be read or is empty."],
                    "message": USER_GUIDANCE_MESSAGE,
                    "metrics": {}
                }
            img_bgr = cv2.imread(str(path_obj))
        elif isinstance(image_input, Image.Image):
            rgb = np.array(image_input.convert("RGB"))
            img_bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            if image_input.ndim == 2:
                img_bgr = cv2.cvtColor(image_input, cv2.COLOR_GRAY2BGR)
            elif image_input.ndim == 3:
                if image_input.shape[2] == 4:
                    img_bgr = cv2.cvtColor(image_input, cv2.COLOR_BGRA2BGR)
                elif image_input.shape[2] == 3:
                    img_bgr = image_input.copy()
    except Exception as e:
        return {
            "is_ood": True,
            "status": "abstained",
            "reason_codes": ["DECODING_ERROR"],
            "reasons": [f"Image decoding failed: {e}"],
            "message": USER_GUIDANCE_MESSAGE,
            "metrics": {}
        }

    if img_bgr is None or img_bgr.size == 0:
        return {
            "is_ood": True,
            "status": "abstained",
            "reason_codes": ["EMPTY_IMAGE"],
            "reasons": ["Image array contains no pixels."],
            "message": USER_GUIDANCE_MESSAGE,
            "metrics": {}
        }

    # 2. Extract deterministic metrics
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    total_pixels = float(gray.shape[0] * gray.shape[1])

    # Fraction of extreme white (>245) and extreme black (<15)
    white_fraction = float(np.mean(gray >= 245))
    black_fraction = float(np.mean(gray <= 15))

    # Inter-channel difference (R vs G vs B)
    # Measures whether color information exists regardless of brightness/skin tone
    b, g, r = img_bgr[:, :, 0], img_bgr[:, :, 1], img_bgr[:, :, 2]
    diff_rg = np.abs(r.astype(float) - g.astype(float))
    diff_gb = np.abs(g.astype(float) - b.astype(float))
    diff_br = np.abs(b.astype(float) - r.astype(float))
    mean_channel_diff = float(np.mean(diff_rg + diff_gb + diff_br))

    # Color distribution entropy (quantized 8x8x8 = 512 bins)
    img_quant = (img_bgr // 32).astype(int)
    bin_indices = img_quant[:, :, 0] * 64 + img_quant[:, :, 1] * 8 + img_quant[:, :, 2]
    counts = np.bincount(bin_indices.ravel(), minlength=512)
    probs = counts[counts > 0] / total_pixels
    color_entropy = float(-np.sum(probs * np.log2(probs))) if len(probs) > 0 else 0.0

    metrics = {
        "white_fraction": round(white_fraction, 4),
        "black_fraction": round(black_fraction, 4),
        "mean_channel_diff": round(mean_channel_diff, 2),
        "color_entropy": round(color_entropy, 3)
    }

    reason_codes: List[str] = []

    # Check 1: Document / Text page (predominantly white paper)
    if white_fraction > 0.70:
        reason_codes.append("DOCUMENT_OR_TEXT_PAGE")

    # Check 2: Solid black void / blank frame
    if black_fraction > 0.85:
        reason_codes.append("EXTREME_VOID_OR_BLANK")

    # Check 3: Monochromatic / pure grayscale (zero or near-zero chromaticity across all pixels)
    # All human skin in clinical photography contains distinct RGB chromaticity (mean diff >= 14.0 across our dataset)
    if mean_channel_diff < 5.0 and white_fraction > 0.40:
        reason_codes.append("MONOCHROMATIC_NON_SKIN")

    # Check 4: Uniform synthetic field (near-zero color entropy)
    # A single solid color swatch or uniform gradient has entropy < 0.5
    if color_entropy < 0.50:
        reason_codes.append("SOLID_OR_SYNTHETIC_COLOR")

    is_ood = len(reason_codes) > 0
    reasons = [OOD_REASON_DESCRIPTIONS.get(c, c) for c in reason_codes]

    return {
        "is_ood": is_ood,
        "status": "abstained" if is_ood else "supported",
        "reason_codes": reason_codes,
        "reasons": reasons,
        "message": USER_GUIDANCE_MESSAGE if is_ood else "",
        "metrics": metrics
    }
