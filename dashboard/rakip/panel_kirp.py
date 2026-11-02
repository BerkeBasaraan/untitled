"""katman_export.js çıktısındaki tam ekran görüntüsünden her cam paneli köşeleri şeffaf PNG olarak kırpar.

Kullanım: python3 dashboard/rakip/panel_kirp.py
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

DIR = Path(__file__).with_name("katmanlar")
RADIUS, SS = 24, 4  # köşe yarıçapı (px), kenar yumuşatma için örnekleme katsayısı

full = Image.open(DIR / "_paneller-tam.png").convert("RGBA")
layout = json.loads((DIR / "katmanlar.json").read_text(encoding="utf-8"))
for p in layout["panels"]:
    x, y, w, h = (round(p[k]) for k in ("x", "y", "w", "h"))
    crop = full.crop((x, y, x + w, y + h))
    mask = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), RADIUS * SS, fill=255)
    crop.putalpha(mask.resize((w, h), Image.LANCZOS))
    p["file"] = f"panel-{p['id']}.png"
    crop.save(DIR / p["file"])
(DIR / "_paneller-tam.png").unlink()
(DIR / "katmanlar.json").write_text(json.dumps(layout, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(layout["panels"]), "panel kırpıldı")
