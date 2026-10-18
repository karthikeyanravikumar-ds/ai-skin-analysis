from pathlib import Path
import csv
import math
from PIL import Image, ImageDraw, ImageOps, ImageFont

ROOT = Path.cwd()
CSV_PATH = ROOT / "reports" / "m4_candidate_image_families.csv"
OUTPUT_DIR = ROOT / "reports" / "m4_urticaria_family_sheets"

if not CSV_PATH.exists():
    raise SystemExit(f"Missing report: {CSV_PATH}")

with CSV_PATH.open("r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

families = {}

for row in rows:
    if row["class_name"] != "urticaria":
        continue

    family_id = row["family_id"]
    families.setdefault(family_id, []).append(row)

ranked = sorted(
    families.items(),
    key=lambda item: -len(item[1])
)[:10]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    font = ImageFont.truetype("arial.ttf", 14)
except OSError:
    font = ImageFont.load_default()

thumb_w, thumb_h = 240, 180
label_h, padding, columns = 65, 12, 3
cell_w = thumb_w + padding * 2
cell_h = thumb_h + label_h + padding * 2

generated = 0

for family_id, members in ranked:
    rows_count = math.ceil(len(members) / columns)

    sheet = Image.new(
        "RGB",
        (columns * cell_w, rows_count * cell_h + 45),
        "#eeeeee"
    )
    draw = ImageDraw.Draw(sheet)

    draw.text(
        (padding, 12),
        f"{family_id} | {len(members)} candidate images",
        fill="black",
        font=font
    )

    for index, member in enumerate(members):
        path = ROOT / member["relative_path"]

        col = index % columns
        row_index = index // columns

        x = col * cell_w + padding
        y = row_index * cell_h + 40 + padding

        if path.exists():
            try:
                with Image.open(path) as original:
                    image = ImageOps.exif_transpose(
                        original
                    ).convert("RGB")
                    image.thumbnail((thumb_w, thumb_h))

                canvas = Image.new(
                    "RGB", (thumb_w, thumb_h), "white"
                )
                canvas.paste(
                    image,
                    (
                        (thumb_w - image.width) // 2,
                        (thumb_h - image.height) // 2
                    )
                )
                sheet.paste(canvas, (x, y))

            except Exception:
                draw.text(
                    (x, y),
                    "Image could not be opened",
                    fill="red"
                )
        else:
            draw.text(
                (x, y),
                "File not found",
                fill="red"
            )

        label = (
            f'{member["split"]}/{member["class_name"]}/'
            f'{member["filename"]}'
        )

        for line_index in range(0, min(len(label), 140), 32):
            draw.text(
                (
                    x,
                    y + thumb_h + 5
                    + (line_index // 32) * 15
                ),
                label[line_index:line_index + 32],
                fill="black",
                font=font
            )

    output_path = OUTPUT_DIR / f"{family_id}.jpg"
    sheet.save(output_path, quality=90)

    generated += 1
    print(f"Created: {output_path.relative_to(ROOT)}")

print(f"\nGenerated {generated} Urticaria contact sheets.")
print(f"Output: {OUTPUT_DIR.relative_to(ROOT)}")
print("No images or model checkpoints were modified.")
