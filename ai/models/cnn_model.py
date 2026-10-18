import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights


NUM_CLASSES = 7


class SkinDiseaseCNN(nn.Module):

    def __init__(self, num_classes=NUM_CLASSES):

        super().__init__()

        # Load pretrained EfficientNet-B0
        self.backbone = efficientnet_b0(
            weights=EfficientNet_B0_Weights.DEFAULT
        )

        # Get number of input features
        in_features = self.backbone.classifier[1].in_features

        # Replace original ImageNet classifier
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.30),
            nn.Linear(
                in_features,
                num_classes
            )
        )

    def forward(self, x):

        return self.backbone(x)


def create_model():

    model = SkinDiseaseCNN(
        num_classes=NUM_CLASSES
    )

    return model


if __name__ == "__main__":

    print("=" * 70)
    print("AI SKIN ANALYSIS - CNN MODEL VERIFICATION")
    print("=" * 70)

    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "cpu"
    )

    print(f"\nDevice: {device}")

    model = create_model()
    model = model.to(device)

    model.eval()

    # Dummy batch
    dummy_input = torch.randn(
        2,
        3,
        224,
        224
    ).to(device)

    with torch.no_grad():

        output = model(dummy_input)

    print("\nInput shape:")
    print(f"  {dummy_input.shape}")

    print("\nOutput shape:")
    print(f"  {output.shape}")

    print("\nExpected output:")
    print("  [batch_size, 7]")

    if output.shape == (2, NUM_CLASSES):

        print("\nPASS - CNN forward pass successful.")

    else:

        print("\nERROR - Unexpected output shape.")

    print("\nModel parameters:")

    total_params = sum(
        p.numel()
        for p in model.parameters()
    )

    trainable_params = sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )

    print(f"  Total parameters     : {total_params:,}")
    print(f"  Trainable parameters : {trainable_params:,}")

    print("\n" + "=" * 70)
