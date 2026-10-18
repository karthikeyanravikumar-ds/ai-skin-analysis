import torch
from pathlib import Path
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

DATA_DIR = Path("data/split")

IMAGE_SIZE = 224
BATCH_SIZE = 32
NUM_WORKERS = 0

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(10),
    transforms.RandomResizedCrop(
        IMAGE_SIZE,
        scale=(0.90, 1.0)
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

    train_dataset = datasets.ImageFolder(
        DATA_DIR / "train",
        transform=train_transform
    )

    val_dataset = datasets.ImageFolder(
        DATA_DIR / "validation",
        transform=eval_transform
    )

    test_dataset = datasets.ImageFolder(
        DATA_DIR / "test",
        transform=eval_transform
    )

    # ImageFolder determines class IDs alphabetically.
    # Verify that all three datasets use exactly the same mapping.

    if train_dataset.class_to_idx != val_dataset.class_to_idx:
        raise ValueError(
            "Train and validation class mappings do not match!"
        )

    if train_dataset.class_to_idx != test_dataset.class_to_idx:
        raise ValueError(
            "Train and test class mappings do not match!"
        )

    class_to_idx = train_dataset.class_to_idx

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS
    )

    return (
        train_dataset,
        val_dataset,
        test_dataset,
        train_loader,
        val_loader,
        test_loader,
        class_to_idx
    )


if __name__ == "__main__":

    print("=" * 70)
    print("AI SKIN ANALYSIS - PYTORCH DATASET VERIFICATION")
    print("=" * 70)

    (
        train_dataset,
        val_dataset,
        test_dataset,
        train_loader,
        val_loader,
        test_loader,
        class_to_idx
    ) = create_dataloaders()

    print("\nClass mapping:")
    
    for class_name, index in class_to_idx.items():
        print(f"  {index}: {class_name}")

    print("\nDataset sizes:")
    print(f"  Train      : {len(train_dataset)}")
    print(f"  Validation : {len(val_dataset)}")
    print(f"  Test       : {len(test_dataset)}")

    print("\nDataLoader batches:")
    print(f"  Train      : {len(train_loader)}")
    print(f"  Validation : {len(val_loader)}")
    print(f"  Test       : {len(test_loader)}")

    # Test one training batch
    images, labels = next(iter(train_loader))

    print("\nSample training batch:")
    print(f"  Image tensor shape : {images.shape}")
    print(f"  Label tensor shape : {labels.shape}")
    print(f"  Image dtype        : {images.dtype}")
    print(f"  Label dtype        : {labels.dtype}")

    print("\nLabel values in sample batch:")
    print(sorted(set(labels.tolist())))

    print("\nExpected image shape:")
    print(
        f"  [batch, 3, {IMAGE_SIZE}, {IMAGE_SIZE}]"
    )

    print("\nPASS - PyTorch dataset and DataLoaders are working.")

    print("=" * 70)
