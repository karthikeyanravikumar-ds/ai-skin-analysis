import sys
import sys
import csv
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ai.models.cnn_model import SkinDiseaseCNN
from ai.training.dataset_v2 import create_dataloaders


ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "models" / "experiments" / "v2"
REPORT_DIR = ROOT / "reports" / "v2"

BEST_MODEL_PATH = MODEL_DIR / "best_model.pth"
HISTORY_PATH = REPORT_DIR / "training_history.csv"

NUM_CLASSES = 7
EPOCHS = 5
PATIENCE = 3
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4
SEED = 42

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
    # Refuse to overwrite any existing V2 checkpoint or history.
    if BEST_MODEL_PATH.exists():
        raise SystemExit(
            f"Checkpoint already exists: {BEST_MODEL_PATH}\n"
            "Choose a new experiment directory or explicitly back up "
            "the existing checkpoint before proceeding."
        )

    if HISTORY_PATH.exists():
        raise SystemExit(
            f"Training history already exists: {HISTORY_PATH}\n"
            "Preserve it before starting another run."
        )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("=" * 70)
    print("AI SKIN ANALYSIS - V2 TRAINING")
    print("=" * 70)
    print(f"Device: {device}")
    print(f"Epoch limit: {EPOCHS}")
    print(f"Best checkpoint: {BEST_MODEL_PATH}")

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
        raise SystemExit(f"Unexpected class mapping: {class_to_idx}")

    print(
        f"Dataset sizes: train={len(train_dataset)}, "
        f"validation={len(val_dataset)}, test={len(test_dataset)}"
    )

    # Compute inverse-frequency weights from training labels only.
    class_counts = np.bincount(
        [label for _, label in train_dataset.samples],
        minlength=NUM_CLASSES,
    )

    if np.any(class_counts == 0):
        raise SystemExit(
            f"At least one class has no training images: {class_counts}"
        )

    weights = len(train_dataset) / (NUM_CLASSES * class_counts)

    class_weights = torch.tensor(
        weights,
        dtype=torch.float32,
        device=device,
    )

    print("\nTraining class counts and loss weights:")
    for name, index in class_to_idx.items():
        print(
            f"{name:25} count={class_counts[index]:4d} "
            f"weight={class_weights[index].item():.3f}"
        )

    model = SkinDiseaseCNN(num_classes=NUM_CLASSES).to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    scheduler = ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=1,
    )

    history = []
    best_val_f1 = -1.0
    epochs_without_improvement = 0

    for epoch in range(1, EPOCHS + 1):
        epoch_start = time.time()
        model.train()

        train_loss_sum = 0.0
        train_true = []
        train_pred = []

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad(set_to_none=True)

            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            train_loss_sum += loss.item() * images.size(0)
            train_true.extend(labels.detach().cpu().tolist())
            train_pred.extend(
                logits.argmax(dim=1).detach().cpu().tolist()
            )

        train_loss = train_loss_sum / len(train_dataset)
        train_acc = accuracy_score(train_true, train_pred)
        train_f1 = f1_score(
            train_true, train_pred,
            average="macro", zero_division=0
        )

        model.eval()
        val_loss_sum = 0.0
        val_true = []
        val_pred = []

        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)

                logits = model(images)
                loss = criterion(logits, labels)

                val_loss_sum += loss.item() * images.size(0)
                val_true.extend(labels.cpu().tolist())
                val_pred.extend(logits.argmax(dim=1).cpu().tolist())

        val_loss = val_loss_sum / len(val_dataset)
        val_acc = accuracy_score(val_true, val_pred)
        val_f1 = f1_score(
            val_true, val_pred,
            average="macro", zero_division=0
        )
        val_precision = precision_score(
            val_true, val_pred,
            average="macro", zero_division=0
        )
        val_recall = recall_score(
            val_true, val_pred,
            average="macro", zero_division=0
        )

        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]["lr"]
        elapsed = time.time() - epoch_start

        print(f"\nEpoch {epoch}/{EPOCHS} ({elapsed / 60:.1f} min)")
        print(
            f"Train: loss={train_loss:.4f} "
            f"accuracy={train_acc:.4f} macro-F1={train_f1:.4f}"
        )
        print(
            f"Val:   loss={val_loss:.4f} "
            f"accuracy={val_acc:.4f} macro-F1={val_f1:.4f}"
        )
        print(
            f"Val macro-precision={val_precision:.4f} "
            f"macro-recall={val_recall:.4f} "
            f"lr={current_lr:.7f}"
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
            "learning_rate": current_lr,
            "elapsed_seconds": round(elapsed, 2),
        })

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            epochs_without_improvement = 0

            torch.save({
                "model_state_dict": model.state_dict(),
                "class_to_idx": class_to_idx,
                "num_classes": NUM_CLASSES,
                "best_val_macro_f1": best_val_f1,
                "epoch": epoch,
                "architecture": "EfficientNet-B0",
                "experiment": "v2",
            }, BEST_MODEL_PATH)

            print(f"Saved best V2 checkpoint (macro-F1={best_val_f1:.4f})")
        else:
            epochs_without_improvement += 1
            print(
                f"No validation macro-F1 improvement "
                f"({epochs_without_improvement}/{PATIENCE})"
            )

        # Persist progress after every epoch.
        with HISTORY_PATH.open(
            "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=list(history[0].keys())
            )
            writer.writeheader()
            writer.writerows(history)

        if epochs_without_improvement >= PATIENCE:
            print("\nEarly stopping triggered.")
            break

    print("\n" + "=" * 70)
    print("V2 TRAINING FINISHED")
    print("=" * 70)
    print(f"Best validation macro-F1: {best_val_f1:.4f}")
    print(f"Checkpoint: {BEST_MODEL_PATH}")
    print(f"Training history: {HISTORY_PATH}")
    print(
        "\nThe test split has not been evaluated yet. "
        "Evaluation will be a separate step."
    )


if __name__ == "__main__":
    main()


