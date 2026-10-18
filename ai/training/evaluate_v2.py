import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import json
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import numpy as np
import torch

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from ai.models.cnn_model import SkinDiseaseCNN
from ai.training.dataset_v2 import create_dataloaders


MODEL_PATH = ROOT / "models" / "experiments" / "v2" / "best_model.pth"
OUTPUT_DIR = ROOT / "reports" / "v2" / "evaluation"

CLASS_NAMES = [
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts",
]


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Checkpoint not found: {MODEL_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    (
        train_dataset,
        val_dataset,
        test_dataset,
        train_loader,
        val_loader,
        test_loader,
        class_to_idx,
    ) = create_dataloaders()

    expected_mapping = {
        name: index for index, name in enumerate(CLASS_NAMES)
    }

    if class_to_idx != expected_mapping:
        raise ValueError(f"Unexpected class mapping: {class_to_idx}")

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("=" * 70)
    print("AI SKIN ANALYSIS - V2 TEST EVALUATION")
    print("=" * 70)
    print(f"Device: {device}")
    print(f"Test images: {len(test_dataset)}")

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True,
    )

    if checkpoint.get("class_to_idx") != class_to_idx:
        raise ValueError("Checkpoint class mapping does not match dataset.")

    model = SkinDiseaseCNN(num_classes=len(CLASS_NAMES)).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    y_true = []
    y_pred = []

    with torch.inference_mode():
        for batch_index, (images, labels) in enumerate(test_loader, start=1):
            images = images.to(device)
            logits = model(images)

            predictions = logits.argmax(dim=1)

            y_true.extend(labels.tolist())
            y_pred.extend(predictions.cpu().tolist())

            if batch_index % 5 == 0 or batch_index == len(test_loader):
                print(
                    f"Processed {len(y_true)}/{len(test_dataset)} "
                    "test images"
                )

    accuracy = accuracy_score(y_true, y_pred)
    macro_precision = precision_score(
        y_true, y_pred, average="macro", zero_division=0
    )
    macro_recall = recall_score(
        y_true, y_pred, average="macro", zero_division=0
    )
    macro_f1 = f1_score(
        y_true, y_pred, average="macro", zero_division=0
    )

    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(CLASS_NAMES))),
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0,
    )

    print("\nOVERALL TEST METRICS")
    print(f"Accuracy:          {accuracy:.4f} ({accuracy * 100:.2f}%)")
    print(f"Macro-precision:   {macro_precision:.4f}")
    print(f"Macro-recall:      {macro_recall:.4f}")
    print(f"Macro-F1:          {macro_f1:.4f}")

    print("\nPER-CLASS RESULTS")
    print(
        f"{'Class':25} {'Precision':>10} {'Recall':>10} "
        f"{'F1-score':>10} {'Support':>9}"
    )

    for name in CLASS_NAMES:
        metrics = report[name]
        print(
            f"{name:25} "
            f"{metrics['precision']:10.4f} "
            f"{metrics['recall']:10.4f} "
            f"{metrics['f1-score']:10.4f} "
            f"{int(metrics['support']):9d}"
        )

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=list(range(len(CLASS_NAMES))),
    )

    # Save metrics as JSON.
    summary = {
        "checkpoint": str(MODEL_PATH.relative_to(ROOT)),
        "test_images": len(test_dataset),
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "classification_report": report,
        "note": (
            "Preliminary dataset evaluation. Earlier near-duplicate "
            "audit found potential cross-split image leakage; results "
            "may be optimistic and do not establish clinical accuracy."
        ),
    }

    with (OUTPUT_DIR / "test_metrics.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(summary, file, indent=2)

    # Save per-class results as CSV.
    with (OUTPUT_DIR / "per_class_metrics.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "class", "precision", "recall", "f1_score", "support"
        ])

        for name in CLASS_NAMES:
            metrics = report[name]
            writer.writerow([
                name,
                metrics["precision"],
                metrics["recall"],
                metrics["f1-score"],
                int(metrics["support"]),
            ])

    # Save confusion matrix as CSV.
    with (OUTPUT_DIR / "confusion_matrix.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["actual/predicted"] + CLASS_NAMES)

        for index, row in enumerate(cm):
            writer.writerow([CLASS_NAMES[index]] + row.tolist())

    # Plot and save confusion matrix.
    fig, ax = plt.subplots(figsize=(12, 10))
    image = ax.imshow(cm, interpolation="nearest")
    ax.set_title("V2 Model - Test Confusion Matrix")
    fig.colorbar(image, ax=ax)

    positions = np.arange(len(CLASS_NAMES))
    ax.set(
        xticks=positions,
        yticks=positions,
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
        xlabel="Predicted class",
        ylabel="Actual class",
    )

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    threshold = cm.max() / 2 if cm.size else 0

    for row in range(cm.shape[0]):
        for column in range(cm.shape[1]):
            ax.text(
                column,
                row,
                str(cm[row, column]),
                ha="center",
                va="center",
                color="white" if cm[row, column] > threshold else "black",
            )

    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "confusion_matrix.png",
        dpi=200,
        bbox_inches="tight",
    )
    plt.close(fig)

    print("\nEvaluation files saved to:")
    print(OUTPUT_DIR)
    print("\nTest evaluation completed.")
    print(
        "Reminder: metrics may be optimistic because potential "
        "near-duplicate images were found across splits."
    )


if __name__ == "__main__":
    main()
