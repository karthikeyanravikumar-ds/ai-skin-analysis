from pathlib import Path
import csv
import math

from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT = Path.cwd()
IMAGE_DIR = ROOT / "data" / "raw" / "warts"
GROUPS_CSV = ROOT / "reports" / "m4_warts_duplicate_groups.csv"
OUTPUT_DIR = ROOT / "reports" / "m4_warts_contact_sheets"

THUMB_W = 240
THUMB_H = 190
LABEL_H = 65
PADDING = 12
COLUMNS = 3
MAX_GROUPS = 10

if not IMAGE_DIR.is_dir():
    raise SystemExit(f"Image directory not found: {IMAGE_DIR}")

if not GROUPS_CSV.is_file():
    raise SystemExit(f"Duplicate-group report not found: {GROUPS_CSV}")

with GROUPS_CSV.open("r", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    groups = list(reader)

groups.sort(
    key=lambda row: (-int(row["group_size"]), row["group_id"])
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    font = ImageFont.truetype("arial.ttf", 14)
    small_font = ImageFont.truetype("arial.ttf", 12)
except OSError:
    font = ImageFont.load_default()
    small_font = font

def wrap_text(text, max_chars=34):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    return lines

generated = 0

for group in groups[:MAX_GROUPS]:
    group_id = group["group_id"]
    filenames = [
        name.strip()
        for name in group["filenames"].split("|")
        if name.strip()
    ]

    if len(filenames) < 2:
        continue

    rows = math.ceil(len(filenames) / COLUMNS)
    cell_w = THUMB_W + PADDING * 2
    cell_h = THUMB_H + LABEL_H + PADDING * 2

    sheet = Image.new(
        "RGB",
        (COLUMNS * cell_w, rows * cell_h + 48),
        "#eeeeee"
    )
    draw = ImageDraw.Draw(sheet)

    draw.text(
        (PADDING, 12),
        f"{group_id} | {len(filenames)} candidate images",
        fill="#111111",
        font=font
    )

    for index, filename in enumerate(filenames):
        path = IMAGE_DIR / filename

        col = index % COLUMNS
        row = index // COLUMNS

        x = col * cell_w + PADDING
        y = row * cell_h + 42 + PADDING

        draw.rectangle(
            [x - 2, y - 2, x + THUMB_W + 2, y + THUMB_H + 2],
            outline="#aaaaaa",
            width=1
        )

        if path.is_file():
            try:
                with Image.open(path) as original:
                    image = ImageOps.exif_transpose(original).convert("RGB")
                    image.thumbnail((THUMB_W, THUMB_H))

                canvas = Image.new(
                    "RGB",
                    (THUMB_W, THUMB_H),
                    "white"
                )

                offset = (
                    (THUMB_W - image.width) // 2,
                    (THUMB_H - image.height) // 2
                )

                canvas.paste(image, offset)
                sheet.paste(canvas, (x, y))

            except Exception as exc:
                draw.text(
                    (x + 5, y + 10),
                    f"Image error: {type(exc).__name__}",
                    fill="#aa0000",
                    font=small_font
                )
        else:
            draw.text(
                (x + 5, y + 10),
                "FILE NOT FOUND",
                fill="#aa0000",
                font=small_font
            )

        label_y = y + THUMB_H + 6

        for line_index, line in enumerate(
            wrap_text(filename, 34)[:4]
        ):
            draw.text(
                (x, label_y + line_index * 15),
                line,
                fill="#111111",
                font=small_font
            )

    output_file = OUTPUT_DIR / f"{group_id}.jpg"
    sheet.save(output_file, quality=92)

    generated += 1
    print(f"Created: {output_file.relative_to(ROOT)}")

print("\n=== CONTACT SHEET SUMMARY ===")
print(f"Groups processed: {generated}")
print(f"Output directory: {OUTPUT_DIR.relative_to(ROOT)}")
print("Original images and model checkpoints were not modified.")
