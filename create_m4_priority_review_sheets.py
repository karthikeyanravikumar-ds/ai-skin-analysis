from pathlib import Path
from PIL import Image, ImageDraw
import pandas as pd
import math
import textwrap

csv_path = Path("reports/m4_candidate_image_families.csv")
output_dir = Path("reports/m4_priority_review_sheets")
output_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(csv_path)

target_families = ["F0004", "F0008", "F0020", "F0021"]

cell_w = 320
image_h = 220
label_h = 75
cols = 3

for family_id in target_families:
    group = df[df["family_id"] == family_id]

    if group.empty:
        print(f"WARNING: {family_id} not found")
        continue

    records = []

    for _, row in group.iterrows():
        path = Path(str(row["relative_path"]))

        if not path.exists():
            path = Path(str(row["relative_path"]).replace("\\", "/"))

        if not path.exists():
            print(f"Missing image: {row['relative_path']}")
            continue

        try:
            image = Image.open(path).convert("RGB")
            image.thumbnail((cell_w - 12, image_h - 12))

            records.append(
                (image.copy(), str(row["relative_path"]))
            )
        except Exception as exc:
            print(f"Could not read {path}: {exc}")

    if not records:
        print(f"No readable images for {family_id}")
        continue

    rows = math.ceil(len(records) / cols)

    sheet = Image.new(
        "RGB",
        (cols * cell_w, rows * (image_h + label_h)),
        "white",
    )

    draw = ImageDraw.Draw(sheet)

    for index, (image, label) in enumerate(records):
        x = (index % cols) * cell_w
        y = (index // cols) * (image_h + label_h)

        image_x = x + (cell_w - image.width) // 2
        image_y = y + (image_h - image.height) // 2

        sheet.paste(image, (image_x, image_y))

        wrapped = textwrap.wrap(label, width=43)

        draw.text(
            (x + 6, y + image_h + 4),
            "\n".join(wrapped[:4]),
            fill="black",
        )

    output_path = output_dir / f"{family_id}.jpg"
    sheet.save(output_path, quality=92)

    print(f"Created: {output_path} ({len(records)} images)")

print("\nReview sheets generated. No dataset files were modified.")
