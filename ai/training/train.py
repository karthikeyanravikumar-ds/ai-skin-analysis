import os
import sys
import csv
import random

# Add project root to Python path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import torch
import torch.nn as nn

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau

from ai.training.dataset import create_dataloaders
from ai.models.cnn_model import SkinDiseaseCNN


# ============================================================
# CONFIGURATION
# ============================================================

NUM_CLASSES = 7
BATCH_SIZE = 32
EPOCHS = 10

LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4

PATIENCE = 5

MODEL_DIR = "models/trained"
REPORT_DIR = "reports"

BEST_MODEL_PATH = os.path.join(MODEL_DIR, "best_model.pth")
HISTORY_PATH = os.path.join(REPORT_DIR, "training_history.csv")


# ============================================================
# REPRODUCIBILITY
# ============================================================

SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


# ============================================================
# DEVICE
# ============================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("=" * 70)
print("AI SKIN ANALYSIS - CNN TRAINING")
print("=" * 70)

print(f"Device: {device}")

if device.type == "cpu":
    print("CUDA not available - training on CPU")


# ============================================================
# DIRECTORIES
# ============================================================

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# ============================================================
# DATA
# ============================================================

train_dataset, val_dataset, test_dataset, train_loader, val_loader, test_loader, class_to_idx = create_dataloaders()

print("\nClass mapping:")

for class_name, class_id in class_to_idx.items():
    print(f"{class_id}: {class_name}")


# ============================================================
# CLASS COUNTS
# ============================================================

train_dataset = train_loader.dataset

class_counts = [0] * NUM_CLASSES

for _, label in train_dataset.samples:
    class_counts[label] += 1

print("\nTraining class counts:")

for class_name, class_id in class_to_idx.items():
    print(f"{class_id}: {class_name:<25} {class_counts[class_id]}")


# ============================================================
# CLASS WEIGHTS
# ============================================================

total_samples = sum(class_counts)

class_weights = [
    total_samples / (NUM_CLASSES * count)
    for count in class_counts
]

class_weights = torch.tensor(
    class_weights,
    dtype=torch.float32,
    device=device
)

print("\nClass weights:")

for i, weight in enumerate(class_weights):
    print(f"{i}: {weight.item():.4f}")


# ============================================================
# MODEL
# ============================================================

model = SkinDiseaseCNN(num_classes=NUM_CLASSES)
model = model.to(device)

print("\nModel loaded successfully.")


# ============================================================
# LOSS
# ============================================================

criterion = nn.CrossEntropyLoss(
    weight=class_weights
)


# ============================================================
# OPTIMIZER
# ============================================================

optimizer = AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=WEIGHT_DECAY
)


# ============================================================
# LEARNING RATE SCHEDULER
# ============================================================

scheduler = ReduceLROnPlateau(
    optimizer,
    mode="min",
    factor=0.5,
    patience=2
)


# ============================================================
# TRAINING FUNCTION
# ============================================================

def train_one_epoch(model, loader, criterion, optimizer):

    model.train()

    running_loss = 0.0

    all_predictions = []
    all_labels = []

    for images, labels in loader:

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        running_loss += loss.item() * images.size(0)

        predictions = torch.argmax(outputs, dim=1)

        all_predictions.extend(
            predictions.detach().cpu().numpy()
        )

        all_labels.extend(
            labels.detach().cpu().numpy()
        )

    epoch_loss = running_loss / len(loader.dataset)

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

    return epoch_loss, accuracy, macro_f1


# ============================================================
# VALIDATION FUNCTION
# ============================================================

def validate(model, loader, criterion):

    model.eval()

    running_loss = 0.0

    all_predictions = []
    all_labels = []

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)

            predictions = torch.argmax(outputs, dim=1)

            all_predictions.extend(
                predictions.cpu().numpy()
            )

            all_labels.extend(
                labels.cpu().numpy()
            )

    epoch_loss = running_loss / len(loader.dataset)

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

    precision = precision_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    recall = recall_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    return (
        epoch_loss,
        accuracy,
        macro_f1,
        precision,
        recall
    )


# ============================================================
# TRAINING LOOP
# ============================================================

history = []

best_val_f1 = -1.0
epochs_without_improvement = 0

print("\n")
print("=" * 70)
print("STARTING TRAINING")
print("=" * 70)


for epoch in range(1, EPOCHS + 1):

    train_loss, train_acc, train_f1 = train_one_epoch(
        model,
        train_loader,
        criterion,
        optimizer
    )

    (
        val_loss,
        val_acc,
        val_f1,
        val_precision,
        val_recall
    ) = validate(
        model,
        val_loader,
        criterion
    )

    scheduler.step(val_loss)

    current_lr = optimizer.param_groups[0]["lr"]

    print(
        f"\nEpoch [{epoch}/{EPOCHS}]"
    )

    print(
        f"Train Loss: {train_loss:.4f} | "
        f"Train Acc: {train_acc:.4f} | "
        f"Train F1: {train_f1:.4f}"
    )

    print(
        f"Val Loss: {val_loss:.4f} | "
        f"Val Acc: {val_acc:.4f} | "
        f"Val F1: {val_f1:.4f}"
    )

    print(
        f"Val Precision: {val_precision:.4f} | "
        f"Val Recall: {val_recall:.4f}"
    )

    print(
        f"Learning Rate: {current_lr:.7f}"
    )

    history.append({
        "epoch": epoch,
        "train_loss": train_loss,
        "train_accuracy": train_acc,
        "train_macro_f1": train_f1,
        "val_loss": val_loss,
        "val_accuracy": val_acc,
        "val_macro_f1": val_f1,
        "val_macro_precision": val_precision,
        "val_macro_recall": val_recall,
        "learning_rate": current_lr
    })


    # ========================================================
    # SAVE BEST MODEL
    # ========================================================

    if val_f1 > best_val_f1:

        best_val_f1 = val_f1
        epochs_without_improvement = 0

        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "class_to_idx": class_to_idx,
                "num_classes": NUM_CLASSES,
                "best_val_macro_f1": best_val_f1
            },
            BEST_MODEL_PATH
        )

        print(
            f"Best model saved "
            f"(Val Macro-F1: {best_val_f1:.4f})"
        )

    else:

        epochs_without_improvement += 1

        print(
            f"No improvement "
            f"({epochs_without_improvement}/{PATIENCE})"
        )


    # ========================================================
    # EARLY STOPPING
    # ========================================================

    if epochs_without_improvement >= PATIENCE:

        print("\nEarly stopping triggered.")

        break


# ============================================================
# SAVE TRAINING HISTORY
# ============================================================

with open(
    HISTORY_PATH,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=history[0].keys()
    )

    writer.writeheader()

    writer.writerows(history)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n")
print("=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)

print(f"Best Validation Macro-F1: {best_val_f1:.4f}")

print(
    f"Best model saved to:\n"
    f"{BEST_MODEL_PATH}"
)

print(
    f"\nTraining history saved to:\n"
    f"{HISTORY_PATH}"
)

