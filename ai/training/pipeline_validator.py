"""
Training Pipeline Validation and Safety Audit Utility (Task TR-01).

Provides non-destructive verification of training configurations, checkpoint safety guards,
class weight calculations, and hyperparameter integrity for future training experiments.
"""

import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PROTECTED_PRODUCTION_CHECKPOINT = PROJECT_ROOT / "models" / "trained" / "best_model.pth"
PROTECTED_MD5 = "FF106263793F9F0A2FB13F15CEB1437E"
PROTECTED_SIZE = 16367097

CLASS_NAMES = [
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts",
]


def check_production_checkpoint_safety(target_path: Path) -> Dict[str, Any]:
    """
    Ensure no training script can overwrite or mutate the protected production checkpoint.
    """
    target_abs = Path(target_path).resolve()
    protected_abs = PROTECTED_PRODUCTION_CHECKPOINT.resolve()

    if target_abs == protected_abs:
        return {
            "safe": False,
            "error": (
                "CRITICAL SAFETY VIOLATION: Target path points directly to the protected "
                "production model checkpoint ('models/trained/best_model.pth'). "
                "Experiments must use isolated directories under 'models/experiments/<exp_id>'."
            ),
            "target": str(target_abs),
        }
    return {
        "safe": True,
        "target": str(target_abs),
    }


def validate_training_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate training configuration parameters for consistency, safety, and correctness.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Output path validation
    out_path_str = config.get("best_model_path")
    if not out_path_str:
        errors.append("Missing required parameter: 'best_model_path'")
    else:
        out_path = Path(out_path_str)
        safety_check = check_production_checkpoint_safety(out_path)
        if not safety_check["safe"]:
            errors.append(safety_check["error"])

    # 2. Number of classes
    num_classes = config.get("num_classes", 7)
    if num_classes != 7:
        warnings.append(f"num_classes is {num_classes}; production application expects 7 classes.")

    # 3. Epochs and batch size
    epochs = config.get("epochs")
    if not isinstance(epochs, int) or epochs <= 0:
        errors.append(f"Invalid epochs value: {epochs}. Must be a positive integer.")

    batch_size = config.get("batch_size")
    if not isinstance(batch_size, int) or batch_size <= 0:
        errors.append(f"Invalid batch_size value: {batch_size}. Must be a positive integer.")

    # 4. Learning rate & weight decay
    lr = config.get("learning_rate")
    if not isinstance(lr, (int, float)) or lr <= 0 or not math.isfinite(lr):
        errors.append(f"Invalid learning_rate: {lr}. Must be a positive finite float.")
    elif lr > 0.01:
        warnings.append(f"Learning rate {lr} is unusually high for fine-tuning EfficientNet-B0.")

    wd = config.get("weight_decay")
    if wd is not None and (not isinstance(wd, (int, float)) or wd < 0 or not math.isfinite(wd)):
        errors.append(f"Invalid weight_decay: {wd}.")

    # 5. Seed
    seed = config.get("seed")
    if seed is None:
        warnings.append("No seed provided; non-deterministic execution may reduce reproducibility.")
    elif not isinstance(seed, int) or seed < 0:
        errors.append(f"Invalid seed: {seed}. Must be a non-negative integer.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "config": config,
    }


def compute_balanced_class_weights(
    class_counts: List[int],
    num_classes: int = 7,
    clip_max: Optional[float] = 10.0
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """
    Compute inverse-frequency class weights with optional upper clipping to avoid extreme loss spikes.
    """
    if len(class_counts) != num_classes:
        raise ValueError(f"Expected {num_classes} counts, got {len(class_counts)}")

    counts = np.array(class_counts, dtype=np.float64)
    if np.any(counts <= 0):
        raise ValueError("Class counts must be strictly positive.")

    total_samples = float(np.sum(counts))
    raw_weights = total_samples / (num_classes * counts)

    if clip_max is not None:
        raw_weights = np.clip(raw_weights, 0.0, clip_max)

    # Normalize so mean weight is 1.0
    normalized_weights = raw_weights / np.mean(raw_weights)

    weights_dict = {
        CLASS_NAMES[i]: float(normalized_weights[i])
        for i in range(num_classes)
    }

    tensor_weights = torch.tensor(normalized_weights, dtype=torch.float32)
    return tensor_weights, weights_dict


def audit_existing_training_scripts() -> Dict[str, Any]:
    """
    Audit existing training scripts (train.py and train_v2.py) for safety defects and capabilities.
    """
    train_py = PROJECT_ROOT / "ai" / "training" / "train.py"
    train_v2_py = PROJECT_ROOT / "ai" / "training" / "train_v2.py"

    findings = []

    # train.py audit
    if train_py.exists():
        content = train_py.read_text(encoding="utf-8")
        if 'MODEL_DIR = "models/trained"' in content and 'BEST_MODEL_PATH = os.path.join(MODEL_DIR, "best_model.pth")' in content:
            findings.append({
                "script": "ai/training/train.py",
                "severity": "CRITICAL",
                "defect": "Production Checkpoint Overwrite Risk",
                "description": (
                    "train.py saves directly to models/trained/best_model.pth without an existing file check "
                    "or experiment versioning. Executing train.py directly would overwrite the production model."
                ),
            })
        if "torch.cuda.manual_seed_all" not in content:
            findings.append({
                "script": "ai/training/train.py",
                "severity": "MEDIUM",
                "defect": "Incomplete GPU Seed Isolation",
                "description": "CUDA multi-GPU seeds and cuDNN deterministic flags are not configured.",
            })
        if "optimizer.state_dict()" not in content:
            findings.append({
                "script": "ai/training/train.py",
                "severity": "LOW",
                "defect": "Incomplete Checkpoint Metadata",
                "description": "Checkpoints omit optimizer state and training epoch, preventing training resumption.",
            })

    # train_v2.py audit
    if train_v2_py.exists():
        content_v2 = train_v2_py.read_text(encoding="utf-8")
        if "if BEST_MODEL_PATH.exists():" in content_v2:
            findings.append({
                "script": "ai/training/train_v2.py",
                "severity": "INFO",
                "defect": "None (Overwriting Protection Implemented)",
                "description": "train_v2.py correctly checks if the destination checkpoint exists and exits early.",
            })

    return {
        "inspected_scripts": ["ai/training/train.py", "ai/training/train_v2.py"],
        "findings": findings,
    }
