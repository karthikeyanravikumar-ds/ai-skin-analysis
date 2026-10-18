from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import hashlib

ROOT = Path.cwd()

files = [
    ROOT / "data/splits_v2/train/warts/nosie12WartNitrogen4.jpg",
    ROOT / "data/splits_v2/validation/warts/nosie112WartNitrogen4.jpg",
    ROOT / "data/splits_v2/validation/warts/warts-cryotherapy-9.jpeg",
]

thumb_w, thumb_h = 540, 360
header_h = 55
canvas = Image.new("RGB", (thumb_w, (thumb_h + header_h) * len(files)), "white")
draw = ImageDraw.Draw(canvas)

for i, path in enumerate(files):
    if not path.exists():
        print(f"MISSING: {path}")
        continue

    with Image.open(path) as im:
        im = ImageOps.fit(im.convert("RGB"), (thumb_w, thumb_h))
        y = i * (thumb_h + header_h)
        canvas.paste(im, (0, y + header_h))
        draw.text((10, y + 10), path.name, fill="black")

output = ROOT / "reports/splits_v2/wart_candidate_comparison.jpg"
canvas.save(output, quality=95)
print(f"Comparison saved: {output}")
