from pathlib import Path

from torch.utils.data import DataLoader
from torchvision import datasets, transforms

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "splits_v2"

IMAGE_SIZE = 224
BATCH_SIZE = 32
NUM_WORKERS = 0

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

EXPECTED_CLASSES = [
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts",
]

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(10),
    transforms.RandomResizedCrop(
        IMAGE_SIZE,
        scale=(0.90, 1.0),
    ),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])


def create_dataloaders():
    if not DATA_DIR.is_dir():
        raise FileNotFoundError(
            f"V2 split directory not found: {DATA_DIR}"
        )

    train_dataset = datasets.ImageFolder(
        DATA_DIR / "train",
        transform=train_transform,
    )

    val_dataset = datasets.ImageFolder(
        DATA_DIR / "validation",
        transform=eval_transform,
    )

    test_dataset = datasets.ImageFolder(
        DATA_DIR / "test",
        transform=eval_transform,
    )

    expected_mapping = {
        name: index for index, name in enumerate(EXPECTED_CLASSES)
    }

    for name, dataset in [
        ("train", train_dataset),
        ("validation", val_dataset),
        ("test", test_dataset),
    ]:
        if dataset.class_to_idx != expected_mapping:
            raise ValueError(
                f"{name} class mapping mismatch: "
                f"{dataset.class_to_idx}"
            )

    if not len(train_dataset) or not len(val_dataset) or not len(test_dataset):
        raise ValueError("One or more dataset splits are empty.")

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
    )

    return (
        train_dataset,
        val_dataset,
        test_dataset,
        train_loader,
        val_loader,
        test_loader,
        train_dataset.class_to_idx,
    )


if __name__ == "__main__":
    (
        train_dataset,
        val_dataset,
        test_dataset,
        train_loader,
        val_loader,
        test_loader,
        class_to_idx,
    ) = create_dataloaders()

    print("=" * 60)
    print("V2 DATASET VERIFICATION")
    print("=" * 60)
    print(f"Dataset path: {DATA_DIR}")
    print(f"Class mapping: {class_to_idx}")
    print(f"Training images: {len(train_dataset)}")
    print(f"Validation images: {len(val_dataset)}")
    print(f"Testing images: {len(test_dataset)}")
    print(f"Training batches: {len(train_loader)}")
    print(f"Validation batches: {len(val_loader)}")
    print(f"Testing batches: {len(test_loader)}")

    images, labels = next(iter(train_loader))
    print(f"Sample image tensor: {images.shape}")
    print(f"Sample label tensor: {labels.shape}")

    print("\nPASS: V2 dataset loaders are working.")
