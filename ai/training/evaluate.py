import os
import sys
import csv

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import torch
import numpy as np

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix
)

from ai.training.dataset import create_dataloaders
from ai.models.cnn_model import SkinDiseaseCNN


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "models/trained/best_model.pth"
REPORT_DIR = "reports"

os.makedirs(REPORT_DIR, exist_ok=True)

CLASS_NAMES = [
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts"
]


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 70)
print("AI SKIN ANALYSIS - TEST EVALUATION")
print("=" * 70)

print(f"Device: {device}")


# ============================================================
# LOAD DATA
# ============================================================

(
    train_dataset,
    val_dataset,
    test_dataset,
    train_loader,
    val_loader,
    test_loader,
    class_to_idx
) = create_dataloaders()


print("\nTest dataset size:")
print(f"  {len(test_dataset)} images")


# ============================================================
# LOAD MODEL
# ============================================================

checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
    weights_only=False
)

model = SkinDiseaseCNN(num_classes=7)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model = model.to(device)

model.eval()

print("\nBest model loaded successfully.")

print(
    f"Best validation Macro-F1: "
    f"{checkpoint['best_val_macro_f1']:.4f}"
)


# ============================================================
# TEST INFERENCE
# ============================================================

all_labels = []
all_predictions = []
all_probabilities = []

with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(device)

        outputs = model(images)

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        predictions = torch.argmax(
            probabilities,
            dim=1
        )

        all_labels.extend(
            labels.numpy()
        )

        all_predictions.extend(
            predictions.cpu().numpy()
        )

        all_probabilities.extend(
            probabilities.cpu().numpy()
        )


all_labels = np.array(all_labels)
all_predictions = np.array(all_predictions)
all_probabilities = np.array(all_probabilities)


# ============================================================
# OVERALL METRICS
# ============================================================

accuracy = accuracy_score(
    all_labels,
    all_predictions
)

macro_f1 = f1_score(
    all_labels,
    all_predictions,
    average="macro",
    zero_division=0
)

macro_precision = precision_score(
    all_labels,
    all_predictions,
    average="macro",
    zero_division=0
)

macro_recall = recall_score(
    all_labels,
    all_predictions,
    average="macro",
    zero_division=0
)


print("\n")
print("=" * 70)
print("OVERALL TEST RESULTS")
print("=" * 70)

print(f"Test Accuracy       : {accuracy:.4f} ({accuracy * 100:.2f}%)")
print(f"Macro Precision     : {macro_precision:.4f}")
print(f"Macro Recall        : {macro_recall:.4f}")
print(f"Macro F1            : {macro_f1:.4f}")


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

report = classification_report(
    all_labels,
    all_predictions,
    target_names=CLASS_NAMES,
    digits=4,
    zero_division=0
)

print("\n")
print("=" * 70)
print("PER-CLASS CLASSIFICATION REPORT")
print("=" * 70)

print(report)


# ============================================================
# SAVE CLASSIFICATION REPORT
# ============================================================

report_path = os.path.join(
    REPORT_DIR,
    "test_classification_report.txt"
)

with open(
    report_path,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "AI SKIN ANALYSIS - TEST CLASSIFICATION REPORT\n"
    )

    file.write("=" * 70 + "\n\n")

    file.write(
        f"Test Accuracy: {accuracy:.4f}\n"
    )

    file.write(
        f"Macro Precision: {macro_precision:.4f}\n"
    )

    file.write(
        f"Macro Recall: {macro_recall:.4f}\n"
    )

    file.write(
        f"Macro F1: {macro_f1:.4f}\n\n"
    )

    file.write(report)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    all_labels,
    all_predictions,
    labels=list(range(len(CLASS_NAMES)))
)

cm_path = os.path.join(
    REPORT_DIR,
    "confusion_matrix.csv"
)

with open(
    cm_path,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow(
        ["Actual / Predicted"] + CLASS_NAMES
    )

    for class_name, row in zip(
        CLASS_NAMES,
        cm
    ):

        writer.writerow(
            [class_name] + row.tolist()
        )


# ============================================================
# PER-CLASS CSV
# ============================================================

class_report = classification_report(
    all_labels,
    all_predictions,
    target_names=CLASS_NAMES,
    output_dict=True,
    zero_division=0
)

metrics_path = os.path.join(
    REPORT_DIR,
    "per_class_metrics.csv"
)

with open(
    metrics_path,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "class",
        "precision",
        "recall",
        "f1_score",
        "support"
    ])

    for class_name in CLASS_NAMES:

        row = class_report[class_name]

        writer.writerow([
            class_name,
            row["precision"],
            row["recall"],
            row["f1-score"],
            row["support"]
        ])


# ============================================================
# CONFUSION MATRIX DISPLAY
# ============================================================

print("\n")
print("=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print("\nRows = Actual | Columns = Predicted\n")

print(
    " " * 24 +
    " ".join(
        f"{i:^8}" for i in range(len(CLASS_NAMES))
    )
)

for i, row in enumerate(cm):

    print(
        f"{CLASS_NAMES[i]:<24}" +
        " ".join(
            f"{value:^8}" for value in row
        )
    )


# ============================================================
# FILE OUTPUT
# ============================================================

print("\n")
print("=" * 70)
print("EVALUATION FILES SAVED")
print("=" * 70)

print(
    f"Classification report:\n"
    f"{report_path}"
)

print(
    f"\nConfusion matrix:\n"
    f"{cm_path}"
)

print(
    f"\nPer-class metrics:\n"
    f"{metrics_path}"
)

print("\n")
print("=" * 70)
print("TEST EVALUATION COMPLETE")
print("=" * 70)
