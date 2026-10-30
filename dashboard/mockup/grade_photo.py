"""Gemi fotoğrafını panel tasarımına göre yerleştirir ve renklendirir (1920x1080).

Kullanım: python3 dashboard/mockup/grade_photo.py <fotoğraf> [çıktı.png]

Küçük fotoğrafları ekran genişliğine büyütmek bulanık gösterir. Bu yüzden fotoğraf keskin kalacağı boyutta
(SHARP_HEIGHT) üst-ortaya yerleştirilir; kenarları, aynı fotoğrafın büyütülüp bulanıklaştırılmış koyu bir
kopyasına yumuşakça karışır. Fotoğraf küçükse önce upscale_photo.py ile 4 kat büyütün.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

W, H = 1920, 1080
SHARP_HEIGHT = 700     # keskin fotoğrafın tuvaldeki yüksekliği
SHIP_BOTTOM_SRC = 0.72  # fotoğrafta geminin su hattı (yüksekliğe oran)
SHIP_CENTER_SRC = 0.52  # fotoğrafta geminin yatay ortası (genişliğe oran)
SHIP_BOTTOM_DST = 436  # tuvalde su hattının y konumu (kartlar 520'de başlar)
SHIP_CENTER_DST = 1000  # tuvalde geminin yatay ortası
FEATHER = 240          # keskin fotoğrafın kenar yumuşatma genişliği

src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name("teu-gemi-arkaplan.png")
photo = Image.open(src).convert("RGB")


def to_array(im):
    return np.asarray(im, dtype=np.float32) / 255.0


# --- Taban: tüm tuvali kaplayan, bulanık ve koyu kopya (renk ve ışık sürekliliği için) ---
cover = max(W / photo.width, H / photo.height) * 1.1
base = photo.resize((round(photo.width * cover), round(photo.height * cover)), Image.LANCZOS)
left, top = (base.width - W) // 2, round(base.height * SHIP_BOTTOM_SRC - SHIP_BOTTOM_DST)
base = base.crop((left, max(top, 0), left + W, max(top, 0) + H)).filter(ImageFilter.GaussianBlur(28))
canvas = to_array(base) * 0.62

# --- Keskin fotoğraf: üst-ortada, kenarları yumuşak maskeyle ---
scale = SHARP_HEIGHT / photo.height
sharp = photo.resize((round(photo.width * scale), SHARP_HEIGHT), Image.LANCZOS).filter(
    ImageFilter.UnsharpMask(radius=1.2, percent=50, threshold=2))
sx = round(SHIP_CENTER_DST - SHIP_CENTER_SRC * sharp.width)
sy = round(SHIP_BOTTOM_DST - SHIP_BOTTOM_SRC * sharp.height)
s = to_array(sharp)
h, w = s.shape[:2]
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
ramp = lambda d: np.clip(d / FEATHER, 0, 1) ** 1.5
mask = ramp(xx) * ramp(w - 1 - xx) * ramp(h - 1 - yy) * np.clip((yy + sy) / 60 + 1, 0, 1)
x0, y0 = max(sx, 0), max(sy, 0)
x1, y1 = min(sx + w, W), min(sy + h, H)
region = canvas[y0:y1, x0:x1]
m = mask[y0 - sy:y1 - sy, x0 - sx:x1 - sx][..., None]
canvas[y0:y1, x0:x1] = region * (1 - m) + s[y0 - sy:y1 - sy, x0 - sx:x1 - sx] * m

# --- Renk: mavi saat + sıcak vurgu (tasarımın turuncusuyla uyumlu) ---
lum = canvas @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
canvas = lum[..., None] + (canvas - lum[..., None]) * 0.82       # doygunluğu biraz kıs
canvas = np.clip(canvas, 0, 1) ** 1.18 * 0.82                     # hafif koyulaştır
lum = canvas @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
hi = np.clip((lum - 0.25) / 0.45, 0, 1)[..., None]                # açık tonlar → sıcak
canvas = canvas * (1 - hi) + canvas * np.array([1.16, 1.0, 0.8]) * hi
lo = np.clip(1 - lum / 0.25, 0, 1)[..., None]                     # koyu tonlar → derin lacivert
canvas = canvas * (1 - lo) + canvas * np.array([0.85, 0.95, 1.1]) * lo

# --- Işık: sağ üstten alçak güneş, suda yansıma ---
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
glow = np.exp(-(((XX - 1560) / 560) ** 2 + ((YY - 250) / 240) ** 2))[..., None]
canvas = 1 - (1 - canvas) * (1 - np.array([1.0, 0.55, 0.2]) * 0.42 * glow)
streak = np.exp(-(((XX - 1500) / 220) ** 2)) * np.clip((YY - 470) / 60, 0, 1) * np.exp(-((YY - 520) / 160) ** 2)
canvas = 1 - (1 - canvas) * (1 - np.array([1.0, 0.62, 0.3]) * 0.28 * streak[..., None])

Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8)).save(out)
print(out, f"keskin fotoğraf {w}x{h} @ ({sx},{sy})")
