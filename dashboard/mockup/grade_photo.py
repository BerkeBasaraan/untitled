"""Gemi fotoğrafını panel tasarımının ışığına göre renklendirir ve 1920x1080 tuvale yerleştirir.

Kullanım: python3 dashboard/mockup/grade_photo.py <fotoğraf> [çıktı.png]
Gemi, kartların üstünde kalacak şekilde tuvalin üst yarısına oturtulur; alt kısım koyu denizle uzatılır.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

W, H = 1920, 1080
SHIP_BOTTOM_SRC = 0.72   # fotoğrafta geminin su hattı (yüksekliğe oran)
SHIP_BOTTOM_DST = 500    # tuvalde su hattının y konumu (kartlar 520'de başlar)

src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name("teu-gemi-arkaplan.png")

photo = Image.open(src).convert("RGB")
scale = W / photo.width
photo = photo.resize((W, round(photo.height * scale)), Image.LANCZOS).filter(
    ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
top = round(SHIP_BOTTOM_DST - SHIP_BOTTOM_SRC * photo.height)

img = np.asarray(photo, dtype=np.float32) / 255.0

# --- Renk düzenleme: soğuk mavi gündüz → akşam üstü, sıcak vurgu ---
lum = img @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
img = lum[..., None] + (img - lum[..., None]) * 0.62          # doygunluğu kıs
img = np.clip(img, 0, 1) ** 1.45 * 0.62                        # pozlamayı düşür, orta tonları koyulaştır
lum = img @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
hi = np.clip((lum - 0.18) / 0.5, 0, 1)[..., None]              # açık tonlar → sıcak
img = img * (1 - hi) + (img * np.array([1.22, 1.0, 0.72])) * hi
img = img * np.array([1.02, 0.93, 0.82])                       # genel sıcak filtre
img = np.clip(img, 0, 1)

# --- Tuvale yerleştir; fotoğrafın altını koyu denizle uzat ---
canvas = np.zeros((H, W, 3), dtype=np.float32)
y0, y1 = max(top, 0), min(top + img.shape[0], H)
canvas[y0:y1] = img[y0 - top:y1 - top]
if y1 < H:
    sea = img[-40:].mean(axis=(0, 1))
    for y in range(y1, H):
        t = (y - y1) / max(H - y1, 1)
        canvas[y] = sea * (1 - t) + np.array([0.03, 0.03, 0.035]) * t
    blend = 220  # geçişi yumuşat
    for k in range(blend):
        y = y1 - blend + k
        a = k / blend
        canvas[y] = canvas[y] * (1 - a) + sea * a
if y0 > 0:
    canvas[:y0] = canvas[y0]

# --- Işık: sağdan gelen alçak güneş parlaması (ekran karışımı) ---
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
glow = np.exp(-(((xx - 1560) / 620) ** 2 + ((yy - 300) / 260) ** 2))[..., None]
warm = np.array([1.0, 0.52, 0.18]) * 0.55
canvas = 1 - (1 - canvas) * (1 - warm * glow)
# su yüzeyinde yansıma şeridi
streak = np.exp(-(((xx - 1560) / 260) ** 2)) * np.clip((yy - 500) / 120, 0, 1) * np.exp(-((yy - 560) / 200) ** 2)
canvas = 1 - (1 - canvas) * (1 - np.array([1.0, 0.6, 0.25]) * 0.35 * streak[..., None])

Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8)).save(out)
print(out, f"(fotoğraf {photo.width}x{photo.height}, üst kenar y={top})")
