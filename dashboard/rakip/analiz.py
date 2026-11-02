"""Rakip ve Pazar Verileri Excel'ini temizler ve dashboard maketi için özet sayıları üretir.

Kullanım: python3 dashboard/rakip/analiz.py <excel> [çıktı.json]
Power Query'deki temizlik adımlarıyla aynı kuralları uygular (bkz. README).
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

src = sys.argv[1]
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name("ozet.json")
# Göstermelik kur (1 birim = x USD). Gerçek dönüşüm Power Query'de yapılacak; o zamana kadar 1:1.
KUR = {"USD": 1.0, "EUR": 1.0, "GBP": 1.0}
RAKIP_ESLE = {"CULINES": "CUL LINES", "NCA (NORHT CAPE AGENCY)": "NCA", "HIKARU (FEVZI GANDUR)": "HIKARU"}


def sheet(name, header):
    df = pd.read_excel(src, sheet_name=name, header=header)
    df = df.loc[:, [c for c in df.columns if not str(c).startswith("Unnamed")]].dropna(how="all")
    for c in df.columns:
        if df[c].dtype == object or str(df[c].dtype) == "str":
            df[c] = df[c].map(lambda v: re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else v)
            df[c] = df[c].replace({"": None})
    return df


def txt(v, bos=""):
    return v if isinstance(v, str) else bos


def rakip(v):
    v = str(v).strip().upper()
    return RAKIP_ESLE.get(v, v)


def fiyat(v):
    """Sayı veya '2150 - 2350' gibi aralık → orta nokta; '-', 'Kapalı', 'yok', '*' → boş."""
    if isinstance(v, (int, float)) and not pd.isna(v):
        return float(v)
    nums = re.findall(r"\d+(?:[.,]\d+)?", str(v))
    return sum(float(n.replace(",", ".")) for n in nums) / len(nums) if nums else None


def tt(v):
    """Transit süresi: '10-12' → 11; Excel'in tarihe çevirdiği '8-9' → 8.5."""
    if hasattr(v, "month") and hasattr(v, "day"):
        return (v.day + v.month) / 2
    return fiyat(v)


rn = sheet("Rakip Navlun", 3)
rn["Rakip"] = rn["Rakip"].map(rakip)
rn["F20"] = rn["20'"].map(fiyat) * rn["PB"].map(KUR)
rn["F40"] = rn["40'"].map(fiyat) * rn["PB"].map(KUR)
rn["Kapali"] = rn[["20'", "40'"]].apply(lambda r: any(str(x).strip().lower() in ("kapalı", "yok") for x in r), axis=1)
rn["TTg"] = rn["TT"].map(tt)
rn["Yuk"] = rn["Yük Durumu"].replace({"sold out": "Overbooked"})
rn["Aktarma"] = rn["Direkt/Aktarmalı"]
gt = sheet("Gemi Takibi", 4)
gt["Rakip"] = gt["Rakip"].map(rakip)
gt["Direkt/Aktarmalı"] = gt["Direkt/Aktarmalı"].replace({"DİREKT": "Direkt"})
gf = sheet("Genel Fiyat Artışları", 0)
gf["Rakip"] = gf["Rakip"].map(rakip)
pb = sheet("Piyasa Bilgisi", 4)
pb["Rakip"] = pb["Rakip"].map(rakip)

hafta = int(rn["Hafta"].max())
n = len(rn)
guncel = int((rn["Hafta"] >= hafta - 1).sum())
o = {"hafta": hafta, "satir": n, "rakip": int(rn["Rakip"].nunique()),
     "rota": int(rn.groupby(["POL", "POD"]).ngroups),
     "guncel_oran": guncel / n, "bu_hafta": int((rn["Hafta"] == hafta).sum()),
     "yuk_ariyor": int((rn["Yuk"] == "Yük Arıyor/Yerini Dolduramıyor").sum()),
     "overbooked": int((rn["Yuk"] == "Overbooked").sum()),
     "ekipman": int(rn["Yetersiz Ekipman"].notna().sum()),
     "ekipman_20": int(rn["Yetersiz Ekipman"].fillna("").str.contains("20").sum()),
     "kapali": int(rn["Kapali"].sum())}

# Direkt primi: aynı POD'da direkt medyan 40' / aktarmalı medyan 40'
d = rn.dropna(subset=["F40"])
prim = []
for pod, g in d.groupby("POD"):
    a, b = g.loc[g.Aktarma == "Direkt", "F40"], g.loc[g.Aktarma == "Aktarmalı", "F40"]
    if len(a) >= 2 and len(b) >= 2:
        prim.append(a.median() / b.median() - 1)
o["direkt_prim"] = float(pd.Series(prim).median()) if prim else None
tt_d = rn.groupby("Aktarma")["TTg"].median().to_dict()
o["tt_direkt"], o["tt_aktarma"] = tt_d.get("Direkt"), tt_d.get("Aktarmalı")

# Fiyat koridoru: servis × POD, 40' (rota kendi para biriminde)
kor = []
for (srv, pod), g in d.groupby(["Turkon İlgili Servis", "POD"]):
    if len(g) < 3:
        continue
    cheapest = g.loc[g.F40.idxmin(), "Rakip"]
    kor.append({"servis": srv, "pod": pod, "pb": "USD", "min": g.F40.min(), "med": g.F40.median(),
                "max": g.F40.max(), "n": len(g), "en_ucuz": cheapest})
o["koridor"] = sorted(kor, key=lambda r: (r["servis"], -r["med"]))

# USEC: rakip bazında medyan 40' (USD)
us = d[d.POD == "USEC"].groupby("Rakip")["F40"].agg(["median", "count"]).sort_values("median")
o["usec"] = [{"rakip": k, "f40": float(v["median"]), "n": int(v["count"])} for k, v in us.iterrows()]

# Servis bazında pazar sinyalleri
sig = []
for srv, g in rn.groupby("Turkon İlgili Servis"):
    sig.append({"servis": srv, "satir": len(g),
                "yuk_ariyor": int((g.Yuk == "Yük Arıyor/Yerini Dolduramıyor").sum()),
                "ekipman": int(g["Yetersiz Ekipman"].notna().sum()),
                "overbooked": int((g.Yuk == "Overbooked").sum())})
o["sinyal"] = sig

# Fiyat artışları (en yeni 6) ve gemi aksaklıkları
gf["Tarih"] = gf["Ertelenen Tarih"].fillna(gf["Planlanan Başlangıç Tarihi"])
o["artis"] = [{"rakip": r.Rakip, "servis": r["Turkon ilgili Servis"], "liman": txt(r["Liman veya Ülke"]),
               "ad": txt(r["Artış Adı"]), "f20": int(r["20'"]), "f40": int(r["40'"]),
               "tarih": r.Tarih.strftime("%d.%m.%Y"), "durum": txt(r.Durum, "Planlandı")}
              for _, r in gf.sort_values("Tarih", ascending=False).head(6).iterrows()]
o["artis_sayi"], o["artis_ertelendi"] = len(gf), int((gf.Durum == "Ertelendi").sum())
aks = gt[gt["Durum"].notna()]
o["aksaklik"] = len(aks)
o["notlar"] = [{"tarih": r["Veri Giriş Tarihi"].strftime("%d.%m"), "rakip": r.Rakip, "yer": r["Liman veya Ülke"],
                "metin": r["Açıklama"]} for _, r in pb.sort_values("Veri Giriş Tarihi", ascending=False).head(3).iterrows()]
o["gemi_aks"] = [{"hafta": int(r.Hafta), "rakip": r.Rakip, "gemi": txt(r["Gemi Adı"]), "durum": r.Durum}
                 for _, r in aks.sort_values("Hafta", ascending=False).head(4).iterrows()]


def clean(x):
    if isinstance(x, float):
        return round(x, 3)
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean(v) for v in x]
    return x


text = json.dumps(clean(o), ensure_ascii=False, indent=1, allow_nan=False)
out.write_text(text, encoding="utf-8")
out.with_suffix(".js").write_text("window.OZET = " + text + ";\n", encoding="utf-8")  # maket HTML'i için
print(json.dumps({k: v for k, v in clean(o).items() if not isinstance(v, list)}, ensure_ascii=False))
