from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from PIL import Image


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source" / "tab-logo-gold.png"
OUTPUT = ROOT / "td-rrs.zip"


def add(archive: ZipFile, name: str, content: bytes) -> None:
    info = ZipInfo(name, (2024, 8, 8, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    archive.writestr(info, content)


with Image.open(SOURCE) as original:
    logo = original.convert("RGBA")
    logo = logo.crop(logo.getbbox())
    logo.thumbnail((250, 125), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (250, 250), (0, 0, 0, 0))
    canvas.alpha_composite(logo, ((250 - logo.width) // 2, (250 - logo.height) // 2))
    image_bytes = io.BytesIO()
    canvas.save(image_bytes, format="PNG", optimize=True)

metadata = {"pack": {"pack_format": 34, "description": "TD RRS | TerraDivina server resources"}}
font = {"providers": [{"type": "bitmap", "file": "terradivina:font/tab_logo.png", "ascent": 27, "height": 120, "chars": ["\ue000"]}]}
with ZipFile(OUTPUT, "w") as archive:
    add(archive, "pack.mcmeta", json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode())
    add(archive, "assets/minecraft/font/default.json", json.dumps(font, ensure_ascii=False, separators=(",", ":")).encode())
    add(archive, "assets/terradivina/textures/font/tab_logo.png", image_bytes.getvalue())

content = OUTPUT.read_bytes()
print(f"{OUTPUT}: {len(content)} bytes")
print(f"SHA-1 {hashlib.sha1(content).hexdigest()}")
print(f"SHA-256 {hashlib.sha256(content).hexdigest()}")
