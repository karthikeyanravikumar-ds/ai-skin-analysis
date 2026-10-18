"""
Reproducible Evaluation, Metrics & Reliability Assessment Module (Task ML-02).

Provides deterministic, reproducible evaluation of the production SkinDiseaseCNN
checkpoint on held-out test splits, including calibration metrics, confidence
distributions, top-k accuracy, and in-depth misclassification analysis.
"""

import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import cv2
import numpy as np
from PIL import Image
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.models.cnn_model import SkinDiseaseCNN
from ai.training.dataset import eval_transform
from ai.preprocessing.image_quality import assess_image_quality

EXPECTED_CHECKPOINT_PATH = PROJECT_ROOT / "models" / "trained" / "best_model.pth"
EXPECTED_CHECKPOINT_MD5 = "FF106263793F9F0A2FB13F15CEB1437E"
EXPECTED_CHECKPOINT_SIZE = 16367097

CLASS_NAMES = [
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts",
]


def verify_checkpoint_integrity(
    checkpoint_path: Path,
    expected_md5: str = EXPECTED_CHECKPOINT_MD5,
    expected_size: int = EXPECTED_CHECKPOINT_SIZE
) -> Dict[str, Any]:
    """Verify that the model checkpoint exists and matches the exact hash and size."""
    if not checkpoint_path.exists():
        return {
            "valid": False,
            "error": f"Checkpoint does not exist: {checkpoint_path}",
            "actual_md5": None,
            "actual_size": 0,
        }
    
    actual_size = checkpoint_path.stat().st_size
    h = hashlib.md5()
    with open(checkpoint_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    actual_md5 = h.hexdigest().upper()
    
    is_valid = (actual_size == expected_size) and (actual_md5 == expected_md5.upper())
    return {
        "valid": is_valid,
        "path": str(checkpoint_path),
        "actual_md5": actual_md5,
        "expected_md5": expected_md5.upper(),
        "actual_size": actual_size,
        "expected_size": expected_size,
        "size_match": actual_size == expected_size,
        "md5_match": actual_md5 == expected_md5.upper(),
    }


def compute_topk_accuracy(y_true: np.ndarray, y_probs: np.ndarray, k: int = 2) -> float:
    """Compute top-k classification accuracy."""
    if len(y_true) == 0:
        return 0.0
    topk_indices = np.argsort(y_probs, axis=1)[:, -k:]
    correct = [y_true[i] in topk_indices[i] for i in range(len(y_true))]
    return float(np.mean(correct))


def compute_brier_score(y_true: np.ndarray, y_probs: np.ndarray, num_classes: int = 7) -> float:
    """Compute multi-class Brier score: (1/N) * sum_i sum_c (P_ic - Y_ic)^2."""
    if len(y_true) == 0:
        return 0.0
    num_samples = len(y_true)
    y_one_hot = np.zeros((num_samples, num_classes), dtype=np.float64)
    for i, label in enumerate(y_true):
        if 0 <= label < num_classes:
            y_one_hot[i, label] = 1.0
    squared_diff = np.sum((y_probs - y_one_hot) ** 2, axis=1)
    return float(np.mean(squared_diff))


def compute_calibration_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_probs: np.ndarray,
    num_bins: int = 10
) -> Dict[str, Any]:
    """
    Compute Expected Calibration Error (ECE) and Maximum Calibration Error (MCE)
    using maximum softmax probability (MSP) partitioned into equal-width bins.
    """
    if len(y_true) == 0:
        return {"ece": 0.0, "mce": 0.0, "bins": []}

    confidences = np.max(y_probs, axis=1)
    accuracies = (y_pred == y_true).astype(float)
    total_samples = len(y_true)

    bin_edges = np.linspace(0.0, 1.0, num_bins + 1)
    bins_data = []
    ece = 0.0
    mce = 0.0

    for m in range(num_bins):
        bin_lower = bin_edges[m]
        bin_upper = bin_edges[m + 1]

        if m == 0:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
        else:
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)

        bin_count = int(np.sum(in_bin))
        if bin_count > 0:
            bin_acc = float(np.mean(accuracies[in_bin]))
            bin_conf = float(np.mean(confidences[in_bin]))
            bin_gap = abs(bin_acc - bin_conf)
            weighted_gap = (bin_count / total_samples) * bin_gap
            ece += weighted_gap
            mce = max(mce, bin_gap)
        else:
            bin_acc = 0.0
            bin_conf = 0.0
            bin_gap = 0.0

        bins_data.append({
            "bin_index": m,
            "range": [round(float(bin_lower), 2), round(float(bin_upper), 2)],
            "count": bin_count,
            "accuracy": round(bin_acc, 4),
            "confidence": round(bin_conf, 4),
            "calibration_gap": round(bin_gap, 4),
        })

    return {
        "ece": float(ece),
        "mce": float(mce),
        "num_bins": num_bins,
        "bins": bins_data,
    }


def compute_confidence_distributions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_probs: np.ndarray
) -> Dict[str, Any]:
    """Compute summary statistics for confidence across all, correct, and incorrect subsets."""
    confidences = np.max(y_probs, axis=1)
    correct_mask = (y_pred == y_true)
    incorrect_mask = ~correct_mask

    def stats_dict(arr: np.ndarray) -> Dict[str, Any]:
        if len(arr) == 0:
            return {"count": 0, "mean": 0.0, "std": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "p25": 0.0, "p75": 0.0}
        return {
            "count": int(len(arr)),
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "median": float(np.median(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "p25": float(np.percentile(arr, 25)),
            "p75": float(np.percentile(arr, 75)),
        }

    return {
        "all": stats_dict(confidences),
        "correct": stats_dict(confidences[correct_mask]),
        "incorrect": stats_dict(confidences[incorrect_mask]),
    }


def compute_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_probs: np.ndarray,
    class_names: List[str] = CLASS_NAMES
) -> Dict[str, Any]:
    """Calculate all required classification, top-k, Brier, calibration, and distribution metrics."""
    acc = float(accuracy_score(y_true, y_pred))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    macro_p = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_p = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
    macro_r = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_r = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    top1_acc = acc
    top2_acc = compute_topk_accuracy(y_true, y_probs, k=2)
    top3_acc = compute_topk_accuracy(y_true, y_probs, k=3)
    brier_score = compute_brier_score(y_true, y_probs, num_classes=len(class_names))
    calibration = compute_calibration_metrics(y_true, y_pred, y_probs, num_bins=10)
    conf_dist = compute_confidence_distributions(y_true, y_pred, y_probs)

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names)))).tolist()
    cls_report = classification_report(
        y_true,
        y_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0
    )

    per_class = {}
    for c_idx, c_name in enumerate(class_names):
        c_stats = cls_report.get(c_name, {})
        per_class[c_name] = {
            "class_index": c_idx,
            "precision": float(c_stats.get("precision", 0.0)),
            "recall": float(c_stats.get("recall", 0.0)),
            "f1_score": float(c_stats.get("f1-score", 0.0)),
            "support": int(c_stats.get("support", 0)),
        }

    return {
        "overall": {
            "total_samples": len(y_true),
            "accuracy": acc,
            "balanced_accuracy": bal_acc,
            "macro_precision": macro_p,
            "weighted_precision": weighted_p,
            "macro_recall": macro_r,
            "weighted_recall": weighted_r,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "top1_accuracy": top1_acc,
            "top2_accuracy": top2_acc,
            "top3_accuracy": top3_acc,
            "brier_score": brier_score,
            "ece": calibration["ece"],
            "mce": calibration["mce"],
        },
        "per_class": per_class,
        "confusion_matrix": cm,
        "calibration": calibration,
        "confidence_distribution": conf_dist,
    }


def evaluate_dataset_samples(
    model: torch.nn.Module,
    dataset: datasets.ImageFolder,
    device: torch.device,
    batch_size: int = 32
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[Dict[str, Any]]]:
    """
    Run non-destructive inference on the dataset and collect per-sample details,
    probabilities, predictions, and quality indicators.
    """
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    y_true_list = []
    y_pred_list = []
    y_probs_list = []
    sample_records = []

    model.eval()
    with torch.no_grad():
        for batch_idx, (images, labels) in enumerate(loader):
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()
            preds = np.argmax(probs, axis=1)

            labels_np = labels.numpy()
            y_true_list.extend(labels_np)
            y_pred_list.extend(preds)
            y_probs_list.extend(probs)

    y_true = np.array(y_true_list)
    y_pred = np.array(y_pred_list)
    y_probs = np.array(y_probs_list)

    # Collect sample paths and quality signals
    for idx, (img_path, true_label) in enumerate(dataset.samples):
        p = Path(img_path)
        pred_label = int(y_pred[idx])
        probs = y_probs[idx]
        conf = float(probs[pred_label])

        # Top 3 classes
        top3_indices = np.argsort(probs)[-3:][::-1]
        top3 = [
            {
                "class_name": CLASS_NAMES[int(t_idx)],
                "class_index": int(t_idx),
                "probability": float(probs[t_idx])
            }
            for t_idx in top3_indices
        ]

        try:
            rel_p = str(p.relative_to(PROJECT_ROOT))
        except Exception:
            rel_p = str(p)

        sample_records.append({
            "sample_index": idx,
            "path": rel_p,
            "filename": p.name,
            "ground_truth_index": int(true_label),
            "ground_truth_class": CLASS_NAMES[int(true_label)],
            "predicted_index": pred_label,
            "predicted_class": CLASS_NAMES[pred_label],
            "is_correct": bool(pred_label == true_label),
            "confidence": conf,
            "top3": top3,
        })

    return y_true, y_pred, y_probs, sample_records


def audit_vitiligo_misclassifications(
    sample_records: List[Dict[str, Any]],
    audit_summary_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Perform deep-dive analysis of vitiligo misclassifications, specifically
    examining actual vitiligo samples predicted as psoriasis.
    """
    vitiligo_samples = [s for s in sample_records if s["ground_truth_class"] == "vitiligo"]
    total_vitiligo = len(vitiligo_samples)
    vitiligo_correct = [s for s in vitiligo_samples if s["is_correct"]]
    vitiligo_errors = [s for s in vitiligo_samples if not s["is_correct"]]
    vitiligo_to_psoriasis = [s for s in vitiligo_samples if s["predicted_class"] == "psoriasis"]

    # Load near-duplicate cross-split list if available
    near_dupe_files = set()
    if audit_summary_path and audit_summary_path.exists():
        try:
            with open(audit_summary_path, "r", encoding="utf-8") as f:
                audit_data = json.load(f)
            d_cand = audit_data.get("splits", {}).get("data_split", {}).get("perceptual_leakage_candidates_d4", [])
            for c in d_cand:
                if c.get("class_name") == "vitiligo":
                    near_dupe_files.add(Path(c["img_a"]).name)
                    near_dupe_files.add(Path(c["img_b"]).name)
        except Exception:
            pass

    investigated_cases = []
    confidences = []
    blur_variances = []
    brightnesses = []

    for item in vitiligo_to_psoriasis:
        abs_path = PROJECT_ROOT / item["path"]
        blur_val = None
        bright_val = None
        iq_status = "unknown"

        if abs_path.exists():
            try:
                iq = assess_image_quality(abs_path)
                blur_val = iq.get("blur_score")
                bright_val = iq.get("brightness_score")
                iq_status = iq.get("status")
            except Exception:
                pass

        p_idx = item["predicted_index"]
        pso_prob = float(item["confidence"])
        vit_prob = 0.0
        for cand in item["top3"]:
            if cand["class_name"] == "vitiligo":
                vit_prob = cand["probability"]

        is_near_dupe = (item["filename"] in near_dupe_files)

        case_data = {
            "filename": item["filename"],
            "relative_path": item["path"],
            "actual_class": "vitiligo",
            "predicted_class": "psoriasis",
            "psoriasis_confidence": round(pso_prob, 4),
            "vitiligo_probability": round(vit_prob, 4),
            "margin": round(pso_prob - vit_prob, 4),
            "top3": item["top3"],
            "blur_variance": blur_val,
            "brightness": bright_val,
            "iq_status": iq_status,
            "associated_with_near_duplicate": is_near_dupe,
        }
        investigated_cases.append(case_data)
        confidences.append(pso_prob)
        if blur_val is not None:
            blur_variances.append(blur_val)
        if bright_val is not None:
            brightnesses.append(bright_val)

    return {
        "total_vitiligo_test_samples": total_vitiligo,
        "correct_vitiligo_predictions": len(vitiligo_correct),
        "total_vitiligo_errors": len(vitiligo_errors),
        "vitiligo_to_psoriasis_errors": len(vitiligo_to_psoriasis),
        "vitiligo_recall": float(len(vitiligo_correct) / total_vitiligo) if total_vitiligo else 0.0,
        "mean_error_confidence": float(np.mean(confidences)) if confidences else 0.0,
        "min_error_confidence": float(np.min(confidences)) if confidences else 0.0,
        "max_error_confidence": float(np.max(confidences)) if confidences else 0.0,
        "cases": investigated_cases,
    }


def audit_abstention_and_reliability(
    sample_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Audit how the application's confidence tiers and caution flags correspond to
    error detection and abstention on the held-out test split.
    """
    total = len(sample_records)
    total_errors = sum(1 for s in sample_records if not s["is_correct"])

    # Application Tiers: High >= 0.80, Moderate 0.60..0.80, Low < 0.60
    high_conf_samples = [s for s in sample_records if s["confidence"] >= 0.80]
    mod_conf_samples = [s for s in sample_records if 0.60 <= s["confidence"] < 0.80]
    low_conf_samples = [s for s in sample_records if s["confidence"] < 0.60]

    high_conf_errors = sum(1 for s in high_conf_samples if not s["is_correct"])
    mod_conf_errors = sum(1 for s in mod_conf_samples if not s["is_correct"])
    low_conf_errors = sum(1 for s in low_conf_samples if not s["is_correct"])

    # Caution threshold (confidence < 0.80 triggers caution flag in confidence engine)
    caution_samples = [s for s in sample_records if s["confidence"] < 0.80]
    caution_errors_caught = sum(1 for s in caution_samples if not s["is_correct"])

    # Ambiguity margin: top-1 prob minus top-2 prob < 0.15
    narrow_margin_samples = []
    narrow_margin_errors = 0
    for s in sample_records:
        if len(s["top3"]) >= 2:
            margin = s["top3"][0]["probability"] - s["top3"][1]["probability"]
            if margin < 0.15:
                narrow_margin_samples.append(s)
                if not s["is_correct"]:
                    narrow_margin_errors += 1

    return {
        "total_test_samples": total,
        "total_errors": total_errors,
        "error_rate": float(total_errors / total) if total else 0.0,
        "application_tier_breakdown": {
            "high_confidence_tier_ge_0_80": {
                "total": len(high_conf_samples),
                "errors": high_conf_errors,
                "error_rate": float(high_conf_errors / len(high_conf_samples)) if high_conf_samples else 0.0,
            },
            "moderate_confidence_tier_0_60_to_0_80": {
                "total": len(mod_conf_samples),
                "errors": mod_conf_errors,
                "error_rate": float(mod_conf_errors / len(mod_conf_samples)) if mod_conf_samples else 0.0,
            },
            "low_confidence_tier_lt_0_60": {
                "total": len(low_conf_samples),
                "errors": low_conf_errors,
                "error_rate": float(low_conf_errors / len(low_conf_samples)) if low_conf_samples else 0.0,
            },
        },
        "caution_flag_analysis": {
            "total_flagged_for_caution": len(caution_samples),
            "errors_flagged": caution_errors_caught,
            "errors_unflagged_in_high_confidence": high_conf_errors,
            "caution_recall_on_errors": float(caution_errors_caught / total_errors) if total_errors else 0.0,
        },
        "narrow_margin_analysis": {
            "margin_threshold": 0.15,
            "total_narrow_margin": len(narrow_margin_samples),
            "errors_in_narrow_margin": narrow_margin_errors,
        },
        "abstention_architecture": {
            "is_calibrated": False,
            "calibration_method": "None (Raw Maximum Softmax Probability)",
            "hard_abstention_enabled": False,
            "advisory_abstention_enabled": True,
            "image_quality_hard_rejection": True,
        }
    }


def run_reproducible_evaluation(
    model_path: Path = EXPECTED_CHECKPOINT_PATH,
    test_dir: Path = PROJECT_ROOT / "data" / "split" / "test",
    seed: int = 42
) -> Dict[str, Any]:
    """
    Execute full reproducible evaluation workflow for ML-02.
    Ensures deterministic evaluation with random seed and checkpoint verification.
    """
    # 1. Deterministic seeding
    torch.manual_seed(seed)
    np.random.seed(seed)

    # 2. Checkpoint verification
    ckpt_info = verify_checkpoint_integrity(model_path)
    if not ckpt_info["valid"]:
        raise ValueError(f"Checkpoint verification failed: {ckpt_info}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)

    model = SkinDiseaseCNN(num_classes=len(CLASS_NAMES))
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    # 3. Load test dataset
    if not test_dir.exists():
        raise FileNotFoundError(f"Test directory not found: {test_dir}")

    test_dataset = datasets.ImageFolder(test_dir, transform=eval_transform)
    assert test_dataset.classes == CLASS_NAMES, f"Class mismatch: {test_dataset.classes} vs {CLASS_NAMES}"

    # 4. Run evaluation
    y_true, y_pred, y_probs, sample_records = evaluate_dataset_samples(
        model=model,
        dataset=test_dataset,
        device=device,
        batch_size=32
    )

    # 5. Compute metrics
    metrics = compute_all_metrics(y_true, y_pred, y_probs, class_names=CLASS_NAMES)

    # 6. Deep-dive on vitiligo misclassifications
    audit_summary_path = PROJECT_ROOT / "reports" / "audit_summary.json"
    vitiligo_audit = audit_vitiligo_misclassifications(sample_records, audit_summary_path)

    # 7. Reliability and abstention audit
    reliability_audit = audit_abstention_and_reliability(sample_records)

    # 8. All errors summary
    errors_summary = [s for s in sample_records if not s["is_correct"]]

    return {
        "execution_metadata": {
            "task": "ML-02",
            "checkpoint_path": str(model_path.relative_to(PROJECT_ROOT)),
            "checkpoint_md5": ckpt_info["actual_md5"],
            "checkpoint_size_bytes": ckpt_info["actual_size"],
            "test_split_path": str(test_dir.relative_to(PROJECT_ROOT)),
            "total_test_samples": len(test_dataset),
            "device": str(device),
            "seed": seed,
            "best_val_macro_f1_in_ckpt": checkpoint.get("best_val_macro_f1"),
        },
        "metrics": metrics,
        "vitiligo_investigation": vitiligo_audit,
        "reliability_and_abstention": reliability_audit,
        "all_errors": errors_summary,
    }


if __name__ == "__main__":
    print("=" * 70)
    print("AI SKIN ANALYSIS - ML-02 REPRODUCIBLE EVALUATION & RELIABILITY AUDIT")
    print("=" * 70)

    results = run_reproducible_evaluation()

    meta = results["execution_metadata"]
    ov = results["metrics"]["overall"]
    pc = results["metrics"]["per_class"]
    cm = results["metrics"]["confusion_matrix"]
    vit = results["vitiligo_investigation"]
    rel = results["reliability_and_abstention"]

    print(f"\nCheckpoint MD5: {meta['checkpoint_md5']}")
    print(f"Checkpoint Size: {meta['checkpoint_size_bytes']} bytes")
    print(f"Test Samples: {meta['total_test_samples']}")

    print("\n--- REPRODUCED OVERALL METRICS ---")
    print(f"Overall Accuracy:       {ov['accuracy'] * 100:.2f}%")
    print(f"Balanced Accuracy:      {ov['balanced_accuracy'] * 100:.2f}%")
    print(f"Top-1 Accuracy:         {ov['top1_accuracy'] * 100:.2f}%")
    print(f"Top-2 Accuracy:         {ov['top2_accuracy'] * 100:.2f}%")
    print(f"Top-3 Accuracy:         {ov['top3_accuracy'] * 100:.2f}%")
    print(f"Macro Precision:        {ov['macro_precision'] * 100:.2f}%")
    print(f"Macro Recall:           {ov['macro_recall'] * 100:.2f}%")
    print(f"Macro F1 Score:         {ov['macro_f1'] * 100:.2f}%")
    print(f"Weighted F1 Score:      {ov['weighted_f1'] * 100:.2f}%")
    print(f"Multi-class Brier Score:{ov['brier_score']:.4f}")
    print(f"Expected Calib. Error:  {ov['ece'] * 100:.2f}%")
    print(f"Maximum Calib. Error:   {ov['mce'] * 100:.2f}%")

    print("\n--- PER-CLASS METRICS ---")
    for name, data in pc.items():
        print(f"  {name:24s}: P={data['precision']:.4f}, R={data['recall']:.4f}, F1={data['f1_score']:.4f}, N={data['support']}")

    print("\n--- CONFUSION MATRIX (Actual rows x Predicted cols) ---")
    for i, row in enumerate(cm):
        print(f"  {CLASS_NAMES[i]:24s}: {row}")

    print("\n--- VITILIGO-TO-PSORIASIS INVESTIGATION ---")
    print(f"Total Vitiligo Test:          {vit['total_vitiligo_test_samples']}")
    print(f"Correct Vitiligo:             {vit['correct_vitiligo_predictions']}")
    print(f"Vitiligo Recall:              {vit['vitiligo_recall'] * 100:.2f}%")
    print(f"Vitiligo -> Psoriasis Errors: {vit['vitiligo_to_psoriasis_errors']}")
    print(f"Mean Confidence on Errors:    {vit['mean_error_confidence'] * 100:.2f}%")

    print("\n--- RELIABILITY & ABSTENTION AUDIT ---")
    print(f"Total Errors across Test Set: {rel['total_errors']} / {rel['total_test_samples']} ({rel['error_rate'] * 100:.2f}%)")
    tb = rel["application_tier_breakdown"]
    print(f"High Tier (>= 0.80):  {tb['high_confidence_tier_ge_0_80']['total']} samples, {tb['high_confidence_tier_ge_0_80']['errors']} errors")
    print(f"Moderate (0.60-0.80): {tb['moderate_confidence_tier_0_60_to_0_80']['total']} samples, {tb['moderate_confidence_tier_0_60_to_0_80']['errors']} errors")
    print(f"Low Tier (< 0.60):    {tb['low_confidence_tier_lt_0_60']['total']} samples, {tb['low_confidence_tier_lt_0_60']['errors']} errors")

    # Save to reports/reproducible_evaluation_ml02.json
    out_path = PROJECT_ROOT / "reports" / "reproducible_evaluation_ml02.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed evaluation results saved to: {out_path}")
