"""Küçük fotoğrafı yapay zekâ ile 4 kat büyütür (OpenCV EDSR modeli).

Gereken: pip install opencv-contrib-python-headless
Model:   https://raw.githubusercontent.com/Saafke/EDSR_Tensorflow/master/models/EDSR_x4.pb
Kullanım: python3 dashboard/mockup/upscale_photo.py <fotoğraf> <EDSR_x4.pb> <çıktı.png>
"""
import sys
import time

import cv2

src, model, out = sys.argv[1:4]
img = cv2.imread(src)
img = cv2.fastNlMeansDenoisingColored(img, None, 3, 3, 7, 21)  # sıkıştırma izlerini hafifçe temizle
sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel(model)
sr.setModel("edsr", 4)
t = time.time()
up = sr.upsample(img)
cv2.imwrite(out, up)
print(up.shape[1], "x", up.shape[0], f"({time.time() - t:.0f} sn)")
