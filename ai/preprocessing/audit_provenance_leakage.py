"""
Comprehensive Dataset Provenance, Split Integrity, Leakage, and Evaluation Audit Script.
(Task ML-01).

Strictly read-only: does not delete, move, or modify any images, splits, or model checkpoints.
"""

import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set

import imagehash
from PIL import Image
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.models.cnn_model import SkinDiseaseCNN
from ai.training.dataset import eval_transform

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
CLASS_NAMES = [
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_image_folder(folder_path: Path) -> Dict[str, Any]:
    """Scan an image folder and record counts, extensions, validity, and modes."""
    stats = {
        "total_files": 0,
        "valid_images": 0,
        "corrupted_images": 0,
        "extensions": defaultdict(int),
        "modes": defaultdict(int),
        "by_class": defaultdict(int),
        "files": [],
    }

    if not folder_path.exists():
        return stats

    for class_dir in sorted(folder_path.iterdir()):
        if not class_dir.is_dir():
            continue
        c_name = class_dir.name
        for p in sorted(class_dir.rglob("*")):
            if not p.is_file():
                continue
            stats["total_files"] += 1
            ext = p.suffix.lower()
            stats["extensions"][ext] += 1
            if ext in VALID_EXTENSIONS:
                try:
                    with Image.open(p) as img:
                        img.verify()
                    with Image.open(p) as img:
                        w, h = img.size
                        mode = img.mode
                    stats["valid_images"] += 1
                    stats["modes"][mode] += 1
                    stats["by_class"][c_name] += 1
                    stats["files"].append({
                        "path": p,
                        "class_name": c_name,
                        "width": w,
                        "height": h,
                        "mode": mode,
                    })
                except Exception as e:
                    stats["corrupted_images"] += 1
    return stats


def audit_split_integrity_and_leakage(split_base_dir: Path) -> Dict[str, Any]:
    """Audit exact duplicates and perceptual near-duplicates within and across splits."""
    results = {
        "split_counts": {},
        "exact_duplicates": [],
        "cross_split_exact_leakage": [],
        "cross_class_exact_duplicates": [],
        "perceptual_leakage_candidates_d4": [],
        "perceptual_leakage_candidates_d8": [],
    }

    images = []
    sha_map = defaultdict(list)
    phash_list = []

    splits = ["train", "validation", "test"]
    for s in splits:
        s_dir = split_base_dir / s
        if not s_dir.exists():
            continue
        for c_dir in sorted(s_dir.iterdir()):
            if not c_dir.is_dir():
                continue
            c_name = c_dir.name
            count = 0
            for p in sorted(c_dir.rglob("*")):
                if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS:
                    try:
                        sha = sha256_file(p)
                        with Image.open(p) as img:
                            img.load()
                            phash = imagehash.phash(img.convert("RGB"))
                        
                        try:
                            rel_path = str(p.relative_to(PROJECT_ROOT))
                        except Exception:
                            rel_path = str(p)

                        item = {
                            "path": p,
                            "rel_path": rel_path,
                            "split": s,
                            "class_name": c_name,
                            "sha256": sha,
                            "phash": phash,
                        }
                        images.append(item)
                        sha_map[sha].append(item)
                        phash_list.append(item)
                        count += 1
                    except Exception:
                        pass
            results["split_counts"][f"{s}/{c_name}"] = count

    # Exact Duplicates
    for sha, matches in sha_map.items():
        if len(matches) > 1:
            results["exact_duplicates"].append({
                "sha256": sha,
                "count": len(matches),
                "instances": [m["rel_path"] for m in matches],
            })
            splits_involved = {m["split"] for m in matches}
            classes_involved = {m["class_name"] for m in matches}
            if len(splits_involved) > 1:
                results["cross_split_exact_leakage"].append({
                    "sha256": sha,
                    "splits": list(splits_involved),
                    "instances": [m["rel_path"] for m in matches],
                })
            if len(classes_involved) > 1:
                results["cross_class_exact_duplicates"].append({
                    "sha256": sha,
                    "classes": list(classes_involved),
                    "instances": [m["rel_path"] for m in matches],
                })

    # Perceptual Duplicates across splits (within same class)
    by_class = defaultdict(list)
    for it in phash_list:
        by_class[it["class_name"]].append(it)

    for c_name, c_images in by_class.items():
        n = len(c_images)
        for i in range(n):
            for j in range(i + 1, n):
                a = c_images[i]
                b = c_images[j]
                if a["split"] != b["split"]:
                    dist = a["phash"] - b["phash"]
                    if dist <= 4:
                        results["perceptual_leakage_candidates_d4"].append({
                            "class_name": c_name,
                            "distance": dist,
                            "split_a": a["split"],
                            "split_b": b["split"],
                            "img_a": a["rel_path"],
                            "img_b": b["rel_path"],
                        })
                    elif dist <= 8:
                        results["perceptual_leakage_candidates_d8"].append({
                            "class_name": c_name,
                            "distance": dist,
                            "split_a": a["split"],
                            "split_b": b["split"],
                            "img_a": a["rel_path"],
                            "img_b": b["rel_path"],
                        })

    return results


def evaluate_model_on_test_split(model_path: Path, test_dir: Path) -> Dict[str, Any]:
    """Run non-destructive test evaluation on genuine held-out test split."""
    if not model_path.exists():
        return {"error": f"Model checkpoint not found: {model_path}"}
    if not test_dir.exists():
        return {"error": f"Test directory not found: {test_dir}"}

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)

    model = SkinDiseaseCNN(num_classes=7)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    from torchvision import datasets
    from torch.utils.data import DataLoader

    test_dataset = datasets.ImageFolder(test_dir, transform=eval_transform)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)

    y_true = []
    y_pred = []
    y_probs = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, preds = torch.max(outputs, 1)

            y_true.extend(labels.cpu().numpy())
            y_pred.extend(preds.cpu().numpy())
            y_probs.extend(probs.cpu().numpy())

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    acc = float(accuracy_score(y_true, y_pred))
    macro_p = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    macro_r = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    cm = confusion_matrix(y_true, y_pred).tolist()
    report_dict = classification_report(
        y_true, y_pred,
        target_names=[test_dataset.classes[i] for i in sorted(test_dataset.class_to_idx.values())],
        output_dict=True,
        zero_division=0
    )

    return {
        "model_path": str(model_path.relative_to(PROJECT_ROOT)),
        "device": str(device),
        "total_test_images": len(test_dataset),
        "class_to_idx": test_dataset.class_to_idx,
        "accuracy": acc,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "best_val_macro_f1_in_ckpt": checkpoint.get("best_val_macro_f1"),
        "confusion_matrix": cm,
        "classification_report": report_dict,
    }


def run_full_ml01_audit() -> Dict[str, Any]:
    """Execute complete ML-01 audit workflow and return structured audit dictionary."""
    audit_data = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_and_processed": {},
        "splits": {},
        "production_model_evaluation": {},
    }

    # 0. Audit raw and processed folders
    for folder_name in ["raw", "processed", "reprocessed_v2"]:
        folder_p = PROJECT_ROOT / "data" / folder_name
        if folder_p.exists():
            st = audit_image_folder(folder_p)
            # Remove file list from JSON dump to keep summary compact
            audit_data["raw_and_processed"][folder_name] = {
                "total_files": st["total_files"],
                "valid_images": st["valid_images"],
                "corrupted_images": st["corrupted_images"],
                "extensions": dict(st["extensions"]),
                "modes": dict(st["modes"]),
                "by_class": dict(st["by_class"]),
            }

    # 1. Audit data/split
    split_dir = PROJECT_ROOT / "data" / "split"
    audit_data["splits"]["data_split"] = audit_split_integrity_and_leakage(split_dir)

    # 2. Audit data/splits_v2 if present
    splits_v2_dir = PROJECT_ROOT / "data" / "splits_v2"
    if splits_v2_dir.exists():
        audit_data["splits"]["data_splits_v2"] = audit_split_integrity_and_leakage(splits_v2_dir)

    # 3. Evaluate production model
    prod_model_path = PROJECT_ROOT / "models" / "trained" / "best_model.pth"
    test_split_dir = PROJECT_ROOT / "data" / "split" / "test"
    audit_data["production_model_evaluation"] = evaluate_model_on_test_split(prod_model_path, test_split_dir)

    # Write out reports/audit_summary.json
    out_dir = PROJECT_ROOT / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "audit_summary.json"
    
    # We serialize helper to convert non-serializable elements if any
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, default=str)
    
    return audit_data


if __name__ == "__main__":
    print("Running ML-01 Dataset, Leakage & Evaluation Audit...")
    audit = run_full_ml01_audit()
    print("\n--- AUDIT SUMMARY ---")
    print(f"Timestamp: {audit['audit_timestamp']}")
    
    ds = audit["splits"]["data_split"]
    print(f"\ndata/split total exact duplicates: {len(ds['exact_duplicates'])}")
    print(f"data/split cross-split exact leakage: {len(ds['cross_split_exact_leakage'])}")
    print(f"data/split cross-class exact duplicates: {len(ds['cross_class_exact_duplicates'])}")
    print(f"data/split near-duplicate cross-split candidates (dist<=4): {len(ds['perceptual_leakage_candidates_d4'])}")
    print(f"data/split near-duplicate cross-split candidates (dist<=8): {len(ds['perceptual_leakage_candidates_d8'])}")

    eval_res = audit["production_model_evaluation"]
    if "error" not in eval_res:
        print(f"\nProduction Model Test Set Evaluation ({eval_res['total_test_images']} images):")
        print(f"  Accuracy:         {eval_res['accuracy'] * 100:.2f}%")
        print(f"  Macro Precision:  {eval_res['macro_precision'] * 100:.2f}%")
        print(f"  Macro Recall:     {eval_res['macro_recall'] * 100:.2f}%")
        print(f"  Macro F1:         {eval_res['macro_f1'] * 100:.2f}%")
        print(f"  Weighted F1:      {eval_res['weighted_f1'] * 100:.2f}%")
        print(f"\nDetailed Classification Report:")
        for k, v in eval_res["classification_report"].items():
            if isinstance(v, dict):
                print(f"  {k:24s}: Precision={v['precision']:.3f}, Recall={v['recall']:.3f}, F1={v['f1-score']:.3f}, Support={v['support']}")
            else:
                print(f"  {k:24s}: {v}")
    else:
        print(f"Evaluation error: {eval_res['error']}")

