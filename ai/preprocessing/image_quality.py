"""
Technical Image Quality Assessment for AI Skin Analysis.

Evaluates uploaded skin images for computer vision suitability:
- File validity and readability
- Technical resolution suitability
- Blur estimation (Laplacian variance)
- Lighting / Brightness bounds (underexposure / overexposure)
- Basic image array integrity

IMPORTANT:
This is a technical computer-vision heuristic, NOT a clinical or medical quality assessment.
Does NOT modify CNN predictions or model confidence.
"""

import os
import math
from pathlib import Path
from typing import Dict, Any, Union, List, Optional
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


# ============================================================
# CONFIGURABLE TECHNICAL THRESHOLDS
# ============================================================

# Minimum resolution expected for consistent CNN feature extraction
MIN_WIDTH: int = 224
MIN_HEIGHT: int = 224

# Blur threshold using Laplacian variance on grayscale image
# Scores below this threshold suggest noticeable optical blur or camera motion
BLUR_THRESHOLD: float = 50.0

# Brightness bounds using mean pixel intensity on grayscale [0..255]
# Below MIN_BRIGHTNESS indicates severe underexposure/darkness
# Above MAX_BRIGHTNESS indicates severe overexposure/glare
MIN_BRIGHTNESS: float = 30.0
MAX_BRIGHTNESS: float = 225.0


def assess_image_quality(
    image_input: Union[str, Path, np.ndarray, Image.Image],
    min_width: int = MIN_WIDTH,
    min_height: int = MIN_HEIGHT,
    blur_threshold: float = BLUR_THRESHOLD,
    min_brightness: float = MIN_BRIGHTNESS,
    max_brightness: float = MAX_BRIGHTNESS
) -> Dict[str, Any]:
    """
    Perform technical image quality assessment.

    Args:
        image_input: File path, numpy BGR/RGB array, or PIL Image.
        min_width: Minimum acceptable width.
        min_height: Minimum acceptable height.
        blur_threshold: Minimum Laplacian variance for blur check.
        min_brightness: Minimum mean grayscale brightness.
        max_brightness: Maximum mean grayscale brightness.

    Returns:
        Structured dictionary detailing image validity, resolution, blur,
        brightness, overall technical status ('good', 'warning', 'poor'),
        and factual warning messages.
    """
    warnings: List[str] = []

    # --------------------------------------------------------
    # 1. FILE VALIDITY & IMAGE DECODING
    # --------------------------------------------------------
    image_bgr: Optional[np.ndarray] = None
    width: int = 0
    height: int = 0

    try:
        if isinstance(image_input, (str, Path)):
            path_obj = Path(image_input)
            if not path_obj.exists():
                return {
                    "status": "poor",
                    "is_valid": False,
                    "resolution": None,
                    "blur": None,
                    "brightness": None,
                    "warnings": [f"Image file not found: {path_obj}"]
                }

            if not path_obj.is_file() or path_obj.stat().st_size == 0:
                return {
                    "status": "poor",
                    "is_valid": False,
                    "resolution": None,
                    "blur": None,
                    "brightness": None,
                    "warnings": ["Image file is empty or invalid."]
                }

            # Attempt decoding with PIL first to catch corrupted headers
            try:
                with Image.open(path_obj) as pil_img:
                    pil_img.verify()
            except (UnidentifiedImageError, OSError, ValueError) as err:
                return {
                    "status": "poor",
                    "is_valid": False,
                    "resolution": None,
                    "blur": None,
                    "brightness": None,
                    "warnings": [f"Image could not be decoded: {str(err)}"]
                }

            # Read with OpenCV for CV computations
            image_bgr = cv2.imread(str(path_obj))
            if image_bgr is None:
                return {
                    "status": "poor",
                    "is_valid": False,
                    "resolution": None,
                    "blur": None,
                    "brightness": None,
                    "warnings": ["Image could not be decoded by OpenCV."]
                }

        elif isinstance(image_input, Image.Image):
            rgb_arr = np.array(image_input.convert("RGB"))
            image_bgr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

        elif isinstance(image_input, np.ndarray):
            if image_input.size == 0:
                return {
                    "status": "poor",
                    "is_valid": False,
                    "resolution": None,
                    "blur": None,
                    "brightness": None,
                    "warnings": ["Provided image array is empty."]
                }
            if not np.all(np.isfinite(image_input)):
                return {
                    "status": "poor",
                    "is_valid": False,
                    "resolution": None,
                    "blur": None,
                    "brightness": None,
                    "warnings": ["Image array contains non-finite (NaN or Inf) values."]
                }
            if image_input.ndim == 2:
                image_bgr = cv2.cvtColor(image_input, cv2.COLOR_GRAY2BGR)
            elif image_input.ndim == 3:
                image_bgr = image_input
            else:
                return {
                    "status": "poor",
                    "is_valid": False,
                    "resolution": None,
                    "blur": None,
                    "brightness": None,
                    "warnings": [f"Invalid image array dimensions: {image_input.shape}"]
                }
        else:
            return {
                "status": "poor",
                "is_valid": False,
                "resolution": None,
                "blur": None,
                "brightness": None,
                "warnings": ["Unsupported image input type."]
            }

    except Exception as exc:
        return {
            "status": "poor",
            "is_valid": False,
            "resolution": None,
            "blur": None,
            "brightness": None,
            "warnings": [f"Unexpected error during image loading: {str(exc)}"]
        }

    # --------------------------------------------------------
    # 2. IMAGE INTEGRITY & RESOLUTION CHECK
    # --------------------------------------------------------
    if image_bgr is None or image_bgr.size == 0:
        return {
            "status": "poor",
            "is_valid": False,
            "resolution": None,
            "blur": None,
            "brightness": None,
            "warnings": ["Image data is invalid or empty."]
        }

    height, width = image_bgr.shape[:2]
    if width <= 0 or height <= 0:
        return {
            "status": "poor",
            "is_valid": False,
            "resolution": None,
            "blur": None,
            "brightness": None,
            "warnings": ["Image has invalid dimensions."]
        }

    resolution_passed = bool(width >= min_width and height >= min_height)
    if not resolution_passed:
        warnings.append(
            f"Image resolution ({width}x{height}) is below the recommended "
            f"technical threshold ({min_width}x{min_height})."
        )

    resolution_info = {
        "width": int(width),
        "height": int(height),
        "passed": resolution_passed,
        "min_width": int(min_width),
        "min_height": int(min_height)
    }

    # --------------------------------------------------------
    # 3. BLUR CHECK (Laplacian Variance)
    # --------------------------------------------------------
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    lap_raw = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    laplacian_var = float(lap_raw) if math.isfinite(lap_raw) else 0.0
    blur_passed = bool(laplacian_var >= blur_threshold)

    if not blur_passed:
        warnings.append(
            f"Image may be blurry (blur score: {laplacian_var:.1f} < threshold: {blur_threshold:.1f})."
        )

    blur_info = {
        "score": round(laplacian_var, 2),
        "passed": blur_passed,
        "threshold": float(blur_threshold)
    }

    # --------------------------------------------------------
    # 4. BRIGHTNESS CHECK (Mean Grayscale Intensity)
    # --------------------------------------------------------
    bright_raw = float(gray.mean())
    brightness_val = float(bright_raw) if math.isfinite(bright_raw) else 0.0
    brightness_passed = bool(min_brightness <= brightness_val <= max_brightness)

    if brightness_val < min_brightness:
        warnings.append(
            f"Image may be underexposed or too dark (brightness: {brightness_val:.1f} < {min_brightness:.1f})."
        )
    elif brightness_val > max_brightness:
        warnings.append(
            f"Image may be overexposed or too bright (brightness: {brightness_val:.1f} > {max_brightness:.1f})."
        )

    brightness_info = {
        "score": round(brightness_val, 2),
        "passed": brightness_passed,
        "min_threshold": float(min_brightness),
        "max_threshold": float(max_brightness)
    }

    # --------------------------------------------------------
    # 5. OVERALL STATUS DETERMINATION
    # --------------------------------------------------------
    # 'good': All technical checks passed
    # 'warning': Exactly one technical warning (e.g., mild blur or slight low resolution)
    # 'poor': 2 or more technical warnings
    if len(warnings) == 0:
        status = "good"
    elif len(warnings) == 1:
        status = "warning"
    else:
        status = "poor"

    return {
        "status": status,
        "is_valid": True,
        "resolution": resolution_info,
        "blur": blur_info,
        "brightness": brightness_info,
        "warnings": warnings
    }
