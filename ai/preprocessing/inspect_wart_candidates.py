import hashlib
from pathlib import Path
from PIL import Image
import imagehash

files = [
    Path(r"data\splits_v2\train\warts\nosie12WartNitrogen4.jpg"),
    Path(r"data\splits_v2\validation\warts\nosie112WartNitrogen4.jpg"),
    Path(r"data\splits_v2\validation\warts\warts-cryotherapy-9.jpeg"),
]

for path in files:
    if not path.exists():
        print(f"MISSING: {path}")
        continue

    digest = hashlib.sha256(path.read_bytes()).hexdigest()

    with Image.open(path) as image:
        print(f"\nFile: {path.name}")
        print(f"Dimensions: {image.size}")
        print(f"Format: {image.format}")
        print(f"Perceptual hash: {imagehash.phash(image.convert('RGB'))}")
        print(f"SHA-256: {digest}")
