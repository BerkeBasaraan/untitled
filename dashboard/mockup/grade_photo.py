"""Gemi fotoğrafını 1920x1080 tuvali tamamen kaplayacak şekilde yerleştirir ve hafifçe renklendirir.

Kullanım: python3 dashboard/mockup/grade_photo.py <fotoğraf> [çıktı.png]

Fotoğraf genişliğe göre ölçeklenir ve kırpılır; FOCUS_SRC (fotoğrafta, yüksekliğe oran) noktası tuvalde FOCUS_DST
yüksekliğine gelir. Kartlar y=520'de başladığı için geminin konteyner istifi bu çizginin üstünde kalmalı.
Fotoğraf küçükse önce upscale_photo.py ile 4 kat büyütün.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

W, H = 1920, 1080
FOCUS_SRC = 0.33   # fotoğrafta konteyner istifinin üstü
FOCUS_DST = 190    # tuvalde bu noktanın y konumu (başlık yazılarının hemen altı)

src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name("teu-gemi-arkaplan.png")
photo = Image.open(src).convert("RGB")

scale = max(W / photo.width, H / photo.height)
photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS).filter(
    ImageFilter.UnsharpMask(radius=1.5, percent=40, threshold=2))
top = round(FOCUS_SRC * photo.height - FOCUS_DST)
top = min(max(top, 0), photo.height - H)
left = (photo.width - W) // 2
img = np.asarray(photo.crop((left, top, left + W, top + H)), dtype=np.float32) / 255.0

# Hafif düzenleme: fotoğrafın kendi gün batımı ışığı korunur, koyu arayüze uysun diye biraz koyulaştırılır.
lum = img @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
img = lum[..., None] + (img - lum[..., None]) * 0.92   # doygunluğu çok az kıs
img = np.clip(img, 0, 1) ** 1.12 * 0.86                  # hafif koyulaştır, kontrastı koru
img = img * np.array([1.03, 0.99, 0.94])                 # turuncu vurguyla uyum için hafif sıcaklık

Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out)
print(out, f"ölçek {scale:.2f}, kırpma ({left},{top})")
