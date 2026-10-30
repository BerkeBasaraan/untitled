"""TEU Challenge Power BI projesini (.pbip) sahte verilerle üretir.

Çalıştırma:  python3 dashboard/pbip/build_pbip.py
Çıktı:       dashboard/pbip/TEU-Challenge.pbip (+ .Report ve .SemanticModel klasörleri)

Power BI Desktop'ta TEU-Challenge.pbip açılır, Dosya > Farklı kaydet ile .pbix olarak kaydedilir.
"""
import json
import random
import shutil
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "TEU-Challenge"
REPORT = ROOT / f"{NAME}.Report"
MODEL = ROOT / f"{NAME}.SemanticModel"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"
rng = random.Random(2026)
uid = lambda: str(uuid.UUID(int=rng.getrandbits(128), version=4))
hexid = lambda: "%020x" % rng.getrandbits(80)

# Renkler (tasarımdaki sistemle aynı)
ME, PRIMARY, CONTEXT, DARK_GREY = "#EB6834", "#2A78D6", "#C8C6C4", "#8A8886"
ACCENT, ACCENT_2, LIGHT, LIGHT_2 = "#FF7A2F", "#F6B73C", "#F5F2EE", "#B3ADA6"  # Panel (koyu) sayfası
CANVAS, TEXT, TEXT2, ME_ROW = "#F3F2F1", "#252423", "#605E5C", "#FDF0EA"

# ---------------------------------------------------------------- Sahte veri
MANAGERS = {
    "Marmara": "Leyla Güneş", "Ege": "Nil Ateş", "Akdeniz": "Serkan Uysal",
    "İç Anadolu": "Okan Bulut", "Karadeniz": "Murat Akın",
}
TOP = [
    ("Ayşe Kaya", "Marmara", 240), ("Mehmet Tunç", "Ege", 200), ("Can Demir", "Marmara", 186),
    ("Elif Şahin", "İç Anadolu", 172), ("Burak Yıldız", "Akdeniz", 165), ("Zeynep Arslan", "Marmara", 151),
    ("Emre Koç", "Ege", 140), ("Selin Aydın", "Karadeniz", 133), ("Kerem Öztürk", "Marmara", 121),
    ("Deniz Çelik", "Akdeniz", 114), ("Ozan Kurt", "İç Anadolu", 102), ("Merve Polat", "Karadeniz", 96),
    ("Hakan Erdem", "Ege", 88), ("Gizem Acar", "Marmara", 79), ("Tolga Şen", "Akdeniz", 71),
]
REST = [
    "Ali Yılmaz", "Fatma Doğan", "Mustafa Kılıç", "Esra Aslan", "Hüseyin Çetin", "Büşra Kara",
    "İbrahim Özdemir", "Cansu Yavuz", "Oğuz Aksoy", "Ebru Turan", "Serdar Işık", "Pınar Ekinci",
    "Kaan Tekin", "Derya Bozkurt", "Volkan Uçar", "Sibel Duman", "Arda Kaplan", "Melis Sarı",
    "Barış Karaca", "Gamze Yüksel", "Onur Coşkun", "İrem Kurtuluş", "Cem Avcı", "Tuğba Öz",
    "Umut Güler", "Seda Karakaya", "Yusuf Sezer",
]
REGIONS = list(MANAGERS)
TR = str.maketrans("çğıİöşüÇĞÖŞÜ", "cgiiosucgosu")
DEMO_EMAIL = "can.demir@ornek.com"
LAST_DAY = date(2026, 10, 27)
LAST_STAMP = datetime(2026, 10, 27, 14, 32)


def email(name):
    return ".".join(name.translate(TR).lower().split()) + "@ornek.com"


rest_totals = rng.sample(range(20, 69), len(REST))
people = [(n, r, t) for n, r, t in TOP] + [
    (n, REGIONS[i % len(REGIONS)], t) for i, (n, t) in enumerate(zip(REST, rest_totals))
]
workdays = [d for d in (date(2026, 10, 1) + timedelta(i) for i in range(27)) if d.weekday() < 5]


def stamp(day, latest=(18, 0)):
    start, end = 8 * 60 + 30, latest[0] * 60 + latest[1]
    m = rng.randrange(start, end)
    return datetime(day.year, day.month, day.day, m // 60, m % 60, rng.randrange(60))


entries = []  # (kisi_id, zaman, teu)
for pid, (name, _, total) in enumerate(people, start=1):
    fixed = []
    if name == "Can Demir":  # bugün 2 giriş; dün 4. sıradaydı
        fixed = [(datetime(2026, 10, 27, 10, 5, 12), 4), (datetime(2026, 10, 27, 14, 11, 40), 12)]
    remaining = total - sum(t for _, t in fixed)
    days = [d for d in workdays if not (d == LAST_DAY and (fixed or name == "Elif Şahin"))]
    while remaining > 0:
        teu = min(rng.choice([2, 4, 4, 6, 6, 8, 10, 12, 16, 20]), remaining)
        day = rng.choice(days)
        if day == LAST_DAY and teu > 6:  # bugünkü girişler küçük kalsın
            continue
        entries.append((pid, stamp(day, (14, 25) if day == LAST_DAY else (18, 0)), teu))
        remaining -= teu
    entries += [(pid, z, t) for z, t in fixed]
entries.sort(key=lambda e: e[1])


def totals_until(day):
    out = {}
    for pid, z, t in entries:
        if z.date() <= day:
            out[pid] = out.get(pid, 0) + t
    return out


final, yesterday = totals_until(LAST_DAY), totals_until(LAST_DAY - timedelta(1))
rank = lambda tot, pid: 1 + sum(v > tot.get(pid, 0) for v in tot.values())
assert [final[i] for i in range(1, 16)] == [t for _, _, t in TOP]
assert rank(final, 3) == 3 and rank(yesterday, 3) == 4, "Can Demir dün 4., bugün 3. olmalı"
tip_rng = random.Random(40)
tips = [tip_rng.choices(["20' DC", "40' HC", "Reefer"], weights=[5, 4, 1])[0] for _ in entries]

# ---------------------------------------------------------------- Yardımcılar


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def lit(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, (int, float)):
        s = f"{v}D"
    else:
        s = "'" + v.replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def solid(c):
    return {"solid": {"color": lit(c) if isinstance(c, str) else c}}


def col(entity, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def mea(prop, entity="_Olculer"):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def proj(field, display=None):
    inner = field.get("Column") or field.get("Measure")
    entity, prop = inner["Expression"]["SourceRef"]["Entity"], inner["Property"]
    p = {"field": field, "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if display:
        p["displayName"] = display
    return p


def props(**kw):
    return [{"properties": {k: (v if isinstance(v, dict) else lit(v)) for k, v in kw.items()}}]


# ---------------------------------------------------------------- Anlamsal model

def m_lines(text):
    return text.strip("\n").split("\n")


def mrow(values):
    def fmt(v):
        if isinstance(v, datetime):
            return f"#datetime({v.year}, {v.month}, {v.day}, {v.hour}, {v.minute}, {v.second})"
        if isinstance(v, str):
            return '"' + v.replace('"', '""') + '"'
        return str(v)
    return "{" + ", ".join(fmt(v) for v in values) + "}"


kisi_rows = ",\n        ".join(
    mrow([i, n, email(n), r, MANAGERS[r], 250]) for i, (n, r, _) in enumerate(people, start=1)
)
kayit_rows = ",\n        ".join(mrow([i, pid, z, t, tip]) for i, ((pid, z, t), tip) in enumerate(zip(entries, tips), start=1))

M_KISILER = f"""
let
    // Gerçek veride bu adımı kendi personel listenizle (Excel, SharePoint, SQL) değiştirin.
    Kaynak = #table(
        type table [KisiID = Int64.Type, Kisi = text, Email = text, Bolge = text, Yonetici = text, HedefTEU = Int64.Type],
        {{
        {kisi_rows}
        }})
in
    Kaynak
"""
M_CHALLENGE = f"""
let
    // Gerçek veride bu adımı challenge tablonuzla değiştirin (sütunlar: KayitID, KisiID, YuklemeZamani, TEU, KonteynerTipi).
    Kaynak = #table(
        type table [KayitID = Int64.Type, KisiID = Int64.Type, YuklemeZamani = datetime, TEU = Int64.Type, KonteynerTipi = text],
        {{
        {kayit_rows}
        }}),
    Tarihli = Table.AddColumn(Kaynak, "Tarih", each DateTime.Date([YuklemeZamani]), type date),
    Sirali = Table.Sort(Tarihli, {{{{"YuklemeZamani", Order.Descending}}}}),
    Indeksli = Table.AddIndexColumn(Sirali, "SonGirisSirasi", 1, 1, Int64.Type)
in
    Indeksli
"""
M_TARIH = """
let
    Baslangic = #date(2026, 10, 1),
    Bitis = #date(2026, 10, 27),
    Gunler = List.Dates(Baslangic, Duration.Days(Bitis - Baslangic) + 1, #duration(1, 0, 0, 0)),
    Tablo = Table.FromList(Gunler, Splitter.SplitByNothing(), {"Tarih"}),
    Tipli = Table.TransformColumnTypes(Tablo, {{"Tarih", type date}}),
    Donem = Table.AddColumn(Tipli, "Donem", each Text.Proper(Date.ToText([Tarih], [Format = "MMMM yyyy", Culture = "tr-TR"])), type text),
    DonemNo = Table.AddColumn(Donem, "DonemNo", each Date.Year([Tarih]) * 100 + Date.Month([Tarih]), Int64.Type),
    GunEtiket = Table.AddColumn(DonemNo, "GunEtiket", each Text.From(Date.Day([Tarih])) & " " & Date.ToText([Tarih], [Format = "ddd", Culture = "tr-TR"]), type text)
in
    GunEtiket
"""
M_SERI = """
let
    Kaynak = #table(type table [SeriNo = Int64.Type, Seri = text], {
        {1, "Sen"}, {2, "Lider"}, {3, "Bir öndeki"}, {4, "Bir arkadaki"}
    })
in
    Kaynak
"""
M_OLCULER = """
let
    Kaynak = #table(type table [Gizli = text], {})
in
    Kaynak
"""

# (ad, DAX, biçim, açıklama)
MEASURES = [
    ("Toplam TEU", "SUM ( Challenge[TEU] )", "#,0", "Seçili kişi/bölge/dönem için toplam TEU."),
    ("Aktif E-posta", """
VAR upn = LOWER ( USERPRINCIPALNAME () )
VAR kayitli =
    CALCULATE ( COUNTROWS ( Kisiler ), REMOVEFILTERS ( Kisiler ), Kisiler[Email] = upn )
RETURN
    -- Raporu açan kişi listede yoksa (ör. Desktop'ta deneme) demo kullanıcısı gösterilir.
    IF ( kayitli > 0, upn, "%s" )""" % DEMO_EMAIL, None, "Raporu açan kullanıcının e-postası."),
    ("Ben mi", """
VAR em = [Aktif E-posta]
RETURN IF ( SELECTEDVALUE ( Kisiler[Email] ) = em, 1, 0 )""", "0", "Satırdaki kişi raporu açan kişiyse 1."),
    ("Son Veri Günü", "CALCULATE ( MAX ( Challenge[Tarih] ), REMOVEFILTERS ( Challenge ) )", "dd.MM.yyyy",
     "Demo için 'bugün' = verideki son gün. Canlı veride TODAY () kullanın."),
    ("Son Güncelleme", """
"Son güncelleme: "
    & FORMAT ( CALCULATE ( MAX ( Challenge[YuklemeZamani] ), REMOVEFILTERS ( Challenge ) ), "dd.MM.yyyy HH:mm" )""",
     None, None),
    ("Sıra", """
IF (
    ISINSCOPE ( Kisiler[Kisi] ),
    RANKX ( ALLSELECTED ( Kisiler[Kisi] ), [Toplam TEU], , DESC, SKIP )
)""", "0", None),
    ("Liderlik TEU", """
VAR s = [Sıra]
RETURN IF ( s <= 15 || [Ben mi] = 1, [Toplam TEU] )""", "#,0", "İlk 15 kişi + raporu açan kişi."),
    ("Bar Rengi", """
SWITCH ( TRUE (), [Ben mi] = 1, "%s", [Sıra] = 1, "%s", "%s" )""" % (ME, PRIMARY, CONTEXT), None, None),
    ("Satır Rengi", 'IF ( [Ben mi] = 1, "%s", "#FFFFFF" )' % ME_ROW, None, None),
    ("Benim TEU", """
VAR em = [Aktif E-posta]
RETURN
    COALESCE ( CALCULATE ( [Toplam TEU], REMOVEFILTERS ( Kisiler ), Kisiler[Email] = em ), 0 )""", "#,0", None),
    ("Benim Hedef", """
VAR em = [Aktif E-posta]
RETURN CALCULATE ( MAX ( Kisiler[HedefTEU] ), REMOVEFILTERS ( Kisiler ), Kisiler[Email] = em )""", "#,0", None),
    ("Hedef Oranı", "DIVIDE ( [Benim TEU], [Benim Hedef] )", "0%", None),
    ("Hedef Açıklama", """
VAR kalan = [Benim Hedef] - [Benim TEU]
RETURN
    "Hedef " & FORMAT ( [Benim Hedef], "#,0" ) & " TEU · %" & FORMAT ( [Hedef Oranı] * 100, "0" )
        & IF ( kalan > 0, " · " & FORMAT ( kalan, "#,0" ) & " TEU kaldı", " · Hedef tamamlandı" )""", None, None),
    ("Katılımcı Sayısı", "COUNTROWS ( ALLSELECTED ( Kisiler[Kisi] ) )", "0", None),
    ("Benim Sıram", """
VAR benim = [Benim TEU]
RETURN COUNTROWS ( FILTER ( ALLSELECTED ( Kisiler[Kisi] ), [Toplam TEU] > benim ) ) + 1""", "0", None),
    ("Dünkü Sıram", """
VAR d = [Son Veri Günü] - 1
VAR em = [Aktif E-posta]
VAR benimDun =
    CALCULATE ( [Toplam TEU], REMOVEFILTERS ( Kisiler ), Kisiler[Email] = em, Tarih[Tarih] <= d )
RETURN
    COUNTROWS (
        FILTER ( ALLSELECTED ( Kisiler[Kisi] ), CALCULATE ( [Toplam TEU], Tarih[Tarih] <= d ) > benimDun )
    ) + 1""", "0", None),
    ("Sıram Metin", 'FORMAT ( [Benim Sıram], "0" ) & "."', None, None),
    ("Sıra Açıklama", """
VAR bugun = [Benim Sıram]
VAR dun = [Dünkü Sıram]
VAR fark = dun - bugun
VAR degisim =
    SWITCH (
        TRUE (),
        fark > 0, UNICHAR ( 9650 ) & " " & fark & " sıra yükseldin (" & dun & ". → " & bugun & ".)",
        fark < 0, UNICHAR ( 9660 ) & " " & ABS ( fark ) & " sıra düştün (" & dun & ". → " & bugun & ".)",
        "Dünle aynı sıradasın"
    )
RETURN [Katılımcı Sayısı] & " kişi içinde · " & degisim""", None, None),
    ("Üsttekiyle Fark", """
VAR benim = [Benim TEU]
VAR ust = MINX ( FILTER ( ALLSELECTED ( Kisiler[Kisi] ), [Toplam TEU] > benim ), [Toplam TEU] )
RETURN IF ( ISBLANK ( ust ), 0, ust - benim )""", '#,0" TEU"', None),
    ("Üstteki Açıklama", """
VAR benim = [Benim TEU]
VAR t =
    FILTER ( ADDCOLUMNS ( ALLSELECTED ( Kisiler[Kisi] ), "@teu", [Toplam TEU] ), [@teu] > benim )
VAR ustTeu = MINX ( t, [@teu] )
VAR ad = CONCATENATEX ( TOPN ( 1, FILTER ( t, [@teu] = ustTeu ), Kisiler[Kisi], ASC ), Kisiler[Kisi] )
RETURN
    IF (
        ISBLANK ( ustTeu ),
        "Zirvedesin, farkı koru!",
        "Önündeki: " & ad & " · " & FORMAT ( ustTeu, "#,0" ) & " TEU"
    )""", None, None),
    ("Bugün Benim TEU", """
VAR d = [Son Veri Günü]
VAR em = [Aktif E-posta]
RETURN
    COALESCE (
        CALCULATE ( [Toplam TEU], REMOVEFILTERS ( Kisiler ), Kisiler[Email] = em, Tarih[Tarih] = d ),
        0
    )""", '+#,0" TEU";-#,0" TEU";0" TEU"', None),
    ("Bugün Açıklama", """
VAR d = [Son Veri Günü]
VAR teu = CALCULATE ( [Toplam TEU], REMOVEFILTERS ( Kisiler ), Tarih[Tarih] = d )
VAR giris = CALCULATE ( COUNTROWS ( Challenge ), REMOVEFILTERS ( Kisiler ), Tarih[Tarih] = d )
RETURN "Şirket geneli: +" & FORMAT ( teu, "#,0" ) & " TEU · " & giris & " giriş\"""", None, None),
    ("Lider Başlık", """
VAR t = ADDCOLUMNS ( ALLSELECTED ( Kisiler[Kisi] ), "@teu", [Toplam TEU] )
VAR enYuksek = MAXX ( t, [@teu] )
VAR lider = CONCATENATEX ( TOPN ( 1, FILTER ( t, [@teu] = enYuksek ), Kisiler[Kisi], ASC ), Kisiler[Kisi] )
RETURN
    "Lider " & lider & " (" & FORMAT ( enYuksek, "#,0" ) & " TEU) · Sen " & [Benim Sıram] & ". sıradasın\"""",
     None, None),
    ("Yarış TEU", """
VAR seri = SELECTEDVALUE ( Seri[SeriNo] )
VAR gun = MAX ( Tarih[Tarih] )
VAR em = [Aktif E-posta]
VAR t =
    ADDCOLUMNS ( ALLSELECTED ( Kisiler[Kisi] ), "@teu", CALCULATE ( [Toplam TEU], ALLSELECTED ( Tarih ) ) )
VAR benimAd =
    CALCULATE ( SELECTEDVALUE ( Kisiler[Kisi] ), REMOVEFILTERS ( Kisiler ), Kisiler[Email] = em )
VAR benimTeu = MAXX ( FILTER ( t, Kisiler[Kisi] = benimAd ), [@teu] )
VAR benimSira = COUNTROWS ( FILTER ( t, [@teu] > benimTeu ) ) + 1
VAR hedefSira = SWITCH ( seri, 1, benimSira, 2, 1, 3, benimSira - 1, 4, benimSira + 1 )
VAR kisi =
    IF (
        seri = 1,
        benimAd,
        CONCATENATEX (
            TOPN ( 1, FILTER ( t, RANKX ( t, [@teu], , DESC, SKIP ) = hedefSira ), Kisiler[Kisi], ASC ),
            Kisiler[Kisi]
        )
    )
RETURN
    IF (
        gun > [Son Veri Günü] || kisi = "" || hedefSira < 1,
        BLANK (),
        CALCULATE ( [Toplam TEU], REMOVEFILTERS ( Kisiler ), Kisiler[Kisi] = kisi, Tarih[Tarih] <= gun )
    )""", "#,0", "Sen / Lider / bir öndeki / bir arkadaki kişinin kümülatif TEU'su."),
    ("Son Giriş TEU", """
IF ( MAX ( Challenge[SonGirisSirasi] ) <= 6, SUM ( Challenge[TEU] ) )""", "#,0", "Son 6 giriş."),
    ("Lider Bölge Başlık", """
VAR t = ADDCOLUMNS ( ALLSELECTED ( Kisiler[Bolge] ), "@teu", [Toplam TEU] )
VAR enYuksek = MAXX ( t, [@teu] )
RETURN
    CONCATENATEX ( TOPN ( 1, FILTER ( t, [@teu] = enYuksek ), Kisiler[Bolge], ASC ), Kisiler[Bolge] )
        & " bölgesi önde\"""", None, None),
    ("Kişi Sayısı", "COUNTROWS ( Kisiler )", "0", None),
    ("Kişi Başı TEU", "DIVIDE ( [Toplam TEU], [Kişi Sayısı] )", "#,0.0", None),
    ("Bölge Hedef %", "DIVIDE ( [Toplam TEU], SUM ( Kisiler[HedefTEU] ) )", "0%", None),
    ("Hedefe Ulaşan", """
COALESCE ( COUNTROWS ( FILTER ( Kisiler, [Toplam TEU] >= Kisiler[HedefTEU] ) ), 0 )""", "0", None),
    ("Aktif Katılımcı %", """
VAR d = [Son Veri Günü]
VAR aktif =
    COUNTROWS (
        FILTER ( Kisiler, CALCULATE ( COUNTROWS ( Challenge ), Tarih[Tarih] > d - 7, Tarih[Tarih] <= d ) > 0 )
    )
RETURN DIVIDE ( aktif, [Kişi Sayısı] )""", "0%", "Son 7 günde en az bir giriş yapanların oranı."),
    # --- Panel sayfası
    ("Benim Adım", """
VAR em = [Aktif E-posta]
RETURN CALCULATE ( SELECTEDVALUE ( Kisiler[Kisi] ), REMOVEFILTERS ( Kisiler ), Kisiler[Email] = em )""", None, None),
    ("Benim Bölgem", """
VAR em = [Aktif E-posta]
RETURN CALCULATE ( SELECTEDVALUE ( Kisiler[Bolge] ), REMOVEFILTERS ( Kisiler ), Kisiler[Email] = em )""", None, None),
    ("Benim Rolüm", '"Satış · " & [Benim Bölgem]', None, None),
    ("Selamlama", """
VAR ad = [Benim Adım]
VAR ilkAd = LEFT ( ad, SEARCH ( " ", ad & " " ) - 1 )
RETURN "Merhaba " & ilkAd & ", bugün " & [Benim Sıram] & ". sıradasın\"""", None, None),
    ("Hedefe Kalan TEU", "MAX ( 0, [Benim Hedef] - [Benim TEU] )", '#,0" TEU"', None),
    ("Üst Sıra Metin", """
VAR s = [Benim Sıram]
RETURN
    IF ( s = 1, "Zirvedesin, farkı koru!", s - 1 & ". sıraya " & FORMAT ( [Üsttekiyle Fark], "#,0" ) & " TEU" )""",
     None, None),
    ("Haftalık Değişim", """
VAR d = [Son Veri Günü]
VAR buHafta = CALCULATE ( [Benim TEU], Tarih[Tarih] > d - 7, Tarih[Tarih] <= d )
VAR gecen = CALCULATE ( [Benim TEU], Tarih[Tarih] > d - 14, Tarih[Tarih] <= d - 7 )
RETURN FORMAT ( buHafta - gecen, "+#,0;-#,0;0" ) & " TEU geçen haftaya göre\"""", None, None),
    ("Challenge Bitiş", "DATE ( 2026, 10, 31 )", "dd.MM.yyyy", "Challenge'ın son günü; yeni dönemde güncelleyin."),
    ("Kalan İş Günü", """
VAR d = [Son Veri Günü]
VAR bitis = [Challenge Bitiş]
RETURN
    IF ( d >= bitis, 0, COUNTROWS ( FILTER ( CALENDAR ( d + 1, bitis ), WEEKDAY ( [Date], 2 ) < 6 ) ) + 0 )""",
     "0", None),
    ("Günlük Ortalama", """
VAR gunler = COUNTROWS ( FILTER ( ALLSELECTED ( Tarih[Tarih] ), WEEKDAY ( Tarih[Tarih], 2 ) < 6 ) )
RETURN DIVIDE ( [Benim TEU], gunler )""", '#,0.0" TEU"', "İş günü başına ortalama TEU."),
    ("Gereken Tempo", "DIVIDE ( [Hedefe Kalan TEU], [Kalan İş Günü] )", '#,0.0" TEU/gün"', None),
    ("Dönem Etiketi", 'SELECTEDVALUE ( Tarih[Donem], "Tüm dönem" ) & " toplamı TEU"', None, None),
    ("Şirket Alt Metin", """
[Katılımcı Sayısı] & " kişi · " & FORMAT ( COUNTROWS ( Challenge ), "#,0" ) & " giriş\"""", None, None),
    ("Lider Metin", """
VAR t = ADDCOLUMNS ( ALLSELECTED ( Kisiler[Kisi] ), "@teu", [Toplam TEU] )
VAR enYuksek = MAXX ( t, [@teu] )
RETURN
    CONCATENATEX ( TOPN ( 1, FILTER ( t, [@teu] = enYuksek ), Kisiler[Kisi], ASC ), Kisiler[Kisi] )
        & " · " & FORMAT ( enYuksek, "#,0" )""", None, None),
    ("Lider Bölge Metin", """
VAR t = ADDCOLUMNS ( ALLSELECTED ( Kisiler[Bolge] ), "@teu", [Toplam TEU] )
VAR enYuksek = MAXX ( t, [@teu] )
RETURN
    CONCATENATEX ( TOPN ( 1, FILTER ( t, [@teu] = enYuksek ), Kisiler[Bolge], ASC ), Kisiler[Bolge] )
        & " · " & FORMAT ( enYuksek, "#,0" )""", None, None),
    ("Günlük Şirket Rengi", 'IF ( MAX ( Tarih[Tarih] ) = [Son Veri Günü], "%s", "#8C8782" )' % ACCENT, None, None),
    ("Son 7 Gün Benim TEU", """
VAR d = [Son Veri Günü]
VAR g = MAX ( Tarih[Tarih] )
RETURN IF ( g > d - 7 && g <= d, [Benim TEU] )""", "#,0", None),
    ("Son 7 Gün Sen", """
VAR d = [Son Veri Günü]
RETURN IF ( MAX ( Tarih[Tarih] ) > d - 7, CALCULATE ( [Yarış TEU], Seri[SeriNo] = 1 ) )""", "#,0", None),
    ("Son 7 Gün Öndeki", """
VAR d = [Son Veri Günü]
RETURN IF ( MAX ( Tarih[Tarih] ) > d - 7, CALCULATE ( [Yarış TEU], Seri[SeriNo] = 3 ) )""", "#,0", None),
    ("Hedef Etiketi", '"Hedef " & FORMAT ( [Benim Hedef], "#,0" ) & " TEU"', None, None),
    ("Hedef İlerleme Metin", 'FORMAT ( [Benim TEU], "#,0" ) & " / " & FORMAT ( [Benim Hedef], "#,0" ) & " TEU"',
     None, None),
    ("Bölge İçi Metin", """
VAR bolge = [Benim Bölgem]
VAR benim = [Benim TEU]
VAR kisiler =
    CALCULATETABLE ( VALUES ( Kisiler[Kisi] ), REMOVEFILTERS ( Kisiler ), Kisiler[Bolge] = bolge )
VAR sira =
    COUNTROWS ( FILTER ( kisiler, CALCULATE ( [Toplam TEU], REMOVEFILTERS ( Kisiler[Bolge] ) ) > benim ) ) + 1
RETURN bolge & " bölgesinde " & sira & ". sıradasın · " & [Kalan İş Günü] & " iş günü kaldı\"""", None, None),
    ("Kümülatif TEU", """
VAR gun = MAX ( Tarih[Tarih] )
RETURN IF ( gun > [Son Veri Günü], BLANK (), CALCULATE ( [Toplam TEU], Tarih[Tarih] <= gun ) )""", "#,0", None),
]


def column(name, dtype, fmt=None, summarize="none", hidden=False, sort_by=None, date_only=False):
    c = {"name": name, "dataType": dtype, "sourceColumn": name, "lineageTag": uid(), "summarizeBy": summarize}
    if fmt:
        c["formatString"] = fmt
    if hidden:
        c["isHidden"] = True
    if sort_by:
        c["sortByColumn"] = sort_by
    if date_only:
        c["annotations"] = [{"name": "UnderlyingDateTimeDataType", "value": "Date"}]
    return c


def table(name, columns, m, measures=None, hidden=False):
    t = {"name": name, "lineageTag": uid(), "columns": columns,
         "partitions": [{"name": name, "mode": "import", "source": {"type": "m", "expression": m_lines(m)}}]}
    if measures:
        t["measures"] = measures
    if hidden:
        t["isHidden"] = True
    return t


measures = []
for name, dax, fmt, desc in MEASURES:
    m = {"name": name, "expression": m_lines(dax) if "\n" in dax.strip() else dax.strip(), "lineageTag": uid()}
    if fmt:
        m["formatString"] = fmt
    if desc:
        m["description"] = desc
    measures.append(m)

model = {
    "compatibilityLevel": 1567,
    "model": {
        "culture": "tr-TR",
        "sourceQueryCulture": "tr-TR",
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
        "tables": [
            table("_Olculer", [column("Gizli", "string", hidden=True)], M_OLCULER, measures),
            table("Kisiler", [
                column("KisiID", "int64", "0", hidden=True), column("Kisi", "string"), column("Email", "string"),
                column("Bolge", "string"), column("Yonetici", "string"), column("HedefTEU", "int64", "#,0", "sum"),
            ], M_KISILER),
            table("Challenge", [
                column("KayitID", "int64", "0"), column("KisiID", "int64", "0", hidden=True),
                column("YuklemeZamani", "dateTime", "dd.MM.yyyy HH:mm"), column("TEU", "int64", "#,0", "sum"),
                column("KonteynerTipi", "string"),
                column("Tarih", "dateTime", "dd.MM.yyyy", hidden=True, date_only=True),
                column("SonGirisSirasi", "int64", "0", hidden=True),
            ], M_CHALLENGE),
            table("Tarih", [
                column("Tarih", "dateTime", "dd.MM.yyyy", date_only=True),
                column("Donem", "string", sort_by="DonemNo"), column("DonemNo", "int64", "0", hidden=True),
                column("GunEtiket", "string", sort_by="Tarih"),
            ], M_TARIH),
            table("Seri", [column("SeriNo", "int64", "0", hidden=True), column("Seri", "string", sort_by="SeriNo")],
                  M_SERI),
        ],
        "relationships": [
            {"name": uid(), "fromTable": "Challenge", "fromColumn": "KisiID", "toTable": "Kisiler", "toColumn": "KisiID"},
            {"name": uid(), "fromTable": "Challenge", "fromColumn": "Tarih", "toTable": "Tarih", "toColumn": "Tarih"},
        ],
        "annotations": [
            {"name": "PBI_QueryOrder", "value": json.dumps(["_Olculer", "Kisiler", "Challenge", "Tarih", "Seri"])},
            {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
        ],
    },
}

# ---------------------------------------------------------------- Rapor görselleri


def visual(x, y, w, h, vtype, query=None, objects=None, container=None, z=0, sort=None):
    v = {"visualType": vtype}
    if query:
        v["query"] = {"queryState": query}
        if sort:
            v["query"]["sortDefinition"] = {"sort": [{"field": f, "direction": d} for f, d in sort]}
    if objects:
        v["objects"] = objects
    if container:
        v["visualContainerObjects"] = container
    v["drillFilterOtherVisuals"] = True
    return {
        "$schema": f"{SCHEMA}/item/report/definition/visualContainer/2.0.0/schema.json",
        "name": hexid(),
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
        "visual": v,
    }


def title(text=None, measure=None, size=12, subtitle_measure=None, color=TEXT):
    c = {"title": props(show=True, fontSize=size, bold=True, fontColor=solid(color))}
    c["title"][0]["properties"]["text"] = {"expr": measure} if measure else lit(text)
    if subtitle_measure:
        c["subTitle"] = props(show=True, text={"expr": subtitle_measure}, fontSize=10, fontColor=solid(TEXT2))
    return c


def no_chrome():
    return {"background": props(show=False), "border": props(show=False), "dropShadow": props(show=False),
            "title": props(show=False)}


def textbox(x, y, w, h, runs, z=0):
    paragraphs = []
    for text, size, bold, color in runs:
        style = {"fontSize": f"{size}pt", "color": color}
        if bold:
            style["fontWeight"] = "bold"
        paragraphs.append({"textRuns": [{"value": text, "textStyle": style}], "horizontalTextAlignment": "left"})
    v = visual(x, y, w, h, "textbox", objects={"general": [{"properties": {"paragraphs": paragraphs}}]},
               container=no_chrome(), z=z)
    return v


def slicer(x, y, w, h, field, header, z):
    return visual(x, y, w, h, "slicer", {"Values": {"projections": [proj(field)]}},
                  objects={"data": props(mode="Dropdown"),
                           "header": props(show=True, text=header, fontSize=9, fontColor=solid(TEXT2)),
                           "selection": props(singleSelect=False, selectAllCheckboxEnabled=True)},
                  container={"title": props(show=False)}, z=z)


def card(x, y, w, h, measure, label, sub_measure, z, value_size=36, label_color=TEXT2):
    c = title(label, size=12, subtitle_measure=mea(sub_measure) if sub_measure else None, color=label_color)
    return visual(x, y, w, h, "card", {"Values": {"projections": [proj(mea(measure))]}},
                  objects={"labels": props(fontSize=value_size, color=solid(TEXT)),
                           "categoryLabels": props(show=False)},
                  container=c, z=z)


def navigator(z):
    return visual(560, 24, 420, 64, "pageNavigator", objects={
        "fill": [
            {"properties": {"show": lit(True), "fillColor": solid("#FFFFFF"), "transparency": lit(0)},
             "selector": {"id": "default"}},
            {"properties": {"show": lit(True), "fillColor": solid(TEXT), "transparency": lit(0)},
             "selector": {"id": "selected"}},
        ],
        "text": [
            {"properties": {"fontColor": solid(TEXT2), "fontSize": lit(11), "bold": lit(True)},
             "selector": {"id": "default"}},
            {"properties": {"fontColor": solid("#FFFFFF")}, "selector": {"id": "selected"}},
        ],
        "outline": [{"properties": {"show": lit(True), "lineColor": solid("#E1DFDD"), "roundEdge": lit(6)},
                     "selector": {"id": "default"}}],
    }, container=no_chrome(), z=z)


def header(page_title, subtitle):
    return [
        textbox(24, 20, 520, 72, [(page_title, 20, True, TEXT), (subtitle, 10, False, TEXT2)], z=0),
        navigator(1000),
        slicer(1012, 24, 260, 64, col("Tarih", "Donem"), "DÖNEM", 2000),
        slicer(1288, 24, 260, 64, col("Kisiler", "Bolge"), "BÖLGE", 3000),
        visual(1564, 24, 332, 64, "card", {"Values": {"projections": [proj(mea("Son Güncelleme"))]}},
               objects={"labels": props(fontSize=11, color=solid(TEXT)), "categoryLabels": props(show=False)},
               container={"title": props(show=False)}, z=4000),
    ]


def footer(z):
    return textbox(24, 1040, 1872, 32, [(
        "Kaynak: Challenge tablosu (demo verisi) · Turuncu = raporu açan kullanıcı, USERPRINCIPALNAME() · "
        "TEU = yirmi fit eşdeğer birim", 9, False, "#8A8886")], z=z)


def bar_chart(x, y, w, h, category, value, z, title_obj, fill=None, sort_measure=None):
    objects = {
        "labels": props(show=True, fontSize=10, color=solid(TEXT), labelPosition="OutsideEnd"),
        "categoryAxis": props(show=True, fontSize=10, color=solid(TEXT)),
        "valueAxis": props(show=True, gridlineShow=True, gridlineColor=solid("#EDEBE9"), fontSize=9,
                           labelColor=solid("#8A8886"), showAxisTitle=False),
        "legend": props(show=False),
    }
    objects["dataPoint"] = [{"properties": {"fill": solid(fill or PRIMARY)}}]
    if isinstance(fill, dict):  # alan değerine göre koşullu renk
        objects["dataPoint"] = [{"properties": {"fill": {"solid": {"color": {"expr": fill}}}},
                                 "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]
    return visual(x, y, w, h, "clusteredBarChart",
                  {"Category": {"projections": [proj(category)]}, "Y": {"projections": [proj(value)]}},
                  objects=objects, container=title_obj, z=z,
                  sort=[(sort_measure or value, "Descending")])


def page(name, display, visuals, image=None):
    base = REPORT / "definition" / "pages" / name
    background = props(color=solid(CANVAS), transparency=0)
    if image:
        background = props(transparency=0)
        background[0]["properties"]["image"] = {"image": {
            "name": lit(image),
            "url": {"expr": {"ResourcePackageItem": {
                "PackageName": "RegisteredResources", "PackageType": 1, "ItemName": image}}},
            "scaling": lit("Fit"),
        }}
    write(base / "page.json", {
        "$schema": f"{SCHEMA}/item/report/definition/page/2.0.0/schema.json",
        "name": name, "displayName": display, "displayOption": "FitToPage", "height": 1080, "width": 1920,
        "objects": {"background": background,
                    "outspace": props(color=solid("#0B0A09" if image else CANVAS), transparency=0)},
    })
    for v in visuals:
        write(base / "visuals" / v["name"] / "visual.json", v)


def series_color(name, color):
    return {"properties": {"fill": solid(color)},
            "selector": {"data": [{"scopeId": {"Comparison": {
                "ComparisonKind": 0, "Left": col("Seri", "Seri"), "Right": {"Literal": {"Value": f"'{name}'"}}}}}]}}


# Önceki çıktıyı temizle
for folder in (REPORT, MODEL):
    if folder.exists():
        shutil.rmtree(folder)

# Sayfa 1: Liderlik
leaderboard = bar_chart(
    24, 280, 928, 540, col("Kisiler", "Kisi"), mea("Liderlik TEU"), 9000,
    {**title(measure=mea("Lider Başlık"), size=12),
     "subTitle": props(show=True, text="Kişi bazında toplam TEU · ilk 15 + sen · kesikli çizgi: 250 TEU hedef",
                       fontSize=10, fontColor=solid(TEXT2))},
    fill=mea("Bar Rengi"),
)
leaderboard["visual"]["objects"]["y1AxisReferenceLine"] = [{
    "properties": {"show": lit(True), "displayName": lit("Hedef"), "value": lit(250), "lineColor": solid(TEXT2),
                   "transparency": lit(0), "style": lit("dashed"), "width": lit(2), "dataLabelShow": lit(True),
                   "dataLabelColor": solid(TEXT2), "dataLabelText": lit("Name"),
                   "dataLabelHorizontalPosition": lit("left"), "dataLabelVerticalPosition": lit("above")},
    "selector": {"id": "1"}}]

race = visual(968, 280, 928, 540, "lineChart", {
    "Category": {"projections": [proj(col("Tarih", "Tarih"))]},
    "Y": {"projections": [proj(mea("Yarış TEU"), "Kümülatif TEU")]},
    "Series": {"projections": [proj(col("Seri", "Seri"))]},
}, objects={
    "dataPoint": [series_color("Sen", ME), series_color("Lider", PRIMARY),
                  series_color("Bir öndeki", DARK_GREY), series_color("Bir arkadaki", CONTEXT)],
    "lineStyles": props(strokeWidth=3, showMarker=False),
    "legend": props(show=True, position="Top", fontSize=10, labelColor=solid(TEXT2), showTitle=False),
    "categoryAxis": props(show=True, fontSize=9, labelColor=solid("#8A8886"), showAxisTitle=False),
    "valueAxis": props(show=True, gridlineShow=True, gridlineColor=solid("#EDEBE9"), fontSize=9,
                       labelColor=solid("#8A8886"), showAxisTitle=False),
    "labels": props(show=False),
}, container={**title("Yarış: sen, lider ve sana en yakın rakiplerin", size=12),
              "subTitle": props(show=True, text="Kümülatif TEU · günlük", fontSize=10, fontColor=solid(TEXT2))},
    z=10000)

latest = visual(24, 836, 1240, 200, "tableEx", {"Values": {"projections": [
    proj(col("Challenge", "YuklemeZamani"), "Yükleme zamanı"), proj(col("Kisiler", "Kisi"), "Kişi"),
    proj(col("Kisiler", "Bolge"), "Bölge"), proj(col("Kisiler", "Yonetici"), "Yönetici"),
    proj(mea("Son Giriş TEU"), "TEU"),
]}}, objects={
    "values": [{"properties": {"backColor": {"solid": {"color": {"expr": mea("Satır Rengi")}}}},
                "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": q}}
               for q in ["Challenge.YuklemeZamani", "Kisiler.Kisi", "Kisiler.Bolge", "Kisiler.Yonetici",
                         "_Olculer.Son Giriş TEU"]],
    "columnHeaders": props(fontSize=10, fontColor=solid(TEXT2), backColor=solid("#FFFFFF")),
    "grid": props(gridHorizontal=True, gridHorizontalColor=solid("#EDEBE9"), rowPadding=4, textSize=10),
    "total": props(totals=False),
}, container=title("Son girişler", size=12), z=11000, sort=[(col("Challenge", "YuklemeZamani"), "Descending")])

regions = bar_chart(1280, 836, 616, 200, col("Kisiler", "Bolge"), mea("Toplam TEU"), 12000,
                    title(measure=mea("Lider Bölge Başlık"), size=12))

kpis = [
    card(24, 104, 456, 160, "Benim TEU", "Senin TEU'n", "Hedef Açıklama", 5000, label_color=ME),
    card(496, 104, 456, 160, "Sıram Metin", "Sıran", "Sıra Açıklama", 6000),
    card(968, 104, 456, 160, "Üsttekiyle Fark", "Bir üst sıraya kalan", "Üstteki Açıklama", 7000),
    card(1440, 104, 456, 160, "Bugün Benim TEU", "Bugün (sen)", "Bugün Açıklama", 8000),
]
page("liderlik", "Liderlik", header("TEU Challenge", "Bireysel TEU liderlik tablosu · Hedef: kişi başı 250 TEU")
     + kpis + [leaderboard, race, latest, regions, footer(13000)])

# Sayfa 2: Bölgeler
region_kpis = [
    card(24 + i * 472, 104, 456, 160, m, label, None, 5000 + i * 100)
    for i, (m, label) in enumerate([("Toplam TEU", "Toplam TEU"), ("Kişi Başı TEU", "Kişi başı TEU"),
                                    ("Hedefe Ulaşan", "Hedefe ulaşan kişi"),
                                    ("Aktif Katılımcı %", "Aktif katılımcı (son 7 gün)")])
]
region_bar = bar_chart(24, 280, 928, 540, col("Kisiler", "Bolge"), mea("Toplam TEU"), 9000,
                       title(measure=mea("Lider Bölge Başlık"), size=12))
region_line = visual(968, 280, 928, 540, "lineChart", {
    "Category": {"projections": [proj(col("Tarih", "Tarih"))]},
    "Y": {"projections": [proj(mea("Kümülatif TEU"))]},
    "Series": {"projections": [proj(col("Kisiler", "Bolge"))]},
}, objects={
    "legend": props(show=True, position="Top", fontSize=10, labelColor=solid(TEXT2), showTitle=False),
    "lineStyles": props(strokeWidth=2, showMarker=False),
    "categoryAxis": props(show=True, fontSize=9, labelColor=solid("#8A8886"), showAxisTitle=False),
    "valueAxis": props(show=True, gridlineShow=True, gridlineColor=solid("#EDEBE9"), fontSize=9,
                       labelColor=solid("#8A8886"), showAxisTitle=False),
}, container=title("Bölgelerin kümülatif TEU yarışı", size=12), z=10000)
region_table = visual(24, 836, 1872, 200, "tableEx", {"Values": {"projections": [
    proj(col("Kisiler", "Bolge"), "Bölge"), proj(col("Kisiler", "Yonetici"), "Bölge müdürü"),
    proj(mea("Kişi Sayısı"), "Kişi"), proj(mea("Toplam TEU"), "Toplam TEU"),
    proj(mea("Kişi Başı TEU"), "Kişi başı"), proj(mea("Bölge Hedef %"), "Hedef %"),
    proj(mea("Hedefe Ulaşan"), "Hedefe ulaşan"),
]}}, objects={"columnHeaders": props(fontSize=10, fontColor=solid(TEXT2)),
              "grid": props(gridHorizontal=True, gridHorizontalColor=solid("#EDEBE9"), rowPadding=4, textSize=10)},
    container=title("Bölge özeti", size=12), z=11000, sort=[(mea("Toplam TEU"), "Descending")])
page("bolgeler", "Bölgeler", header("TEU Challenge · Bölgeler", "Bölge ve ekip karşılaştırması")
     + region_kpis + [region_bar, region_line, region_table, footer(13000)])

# Sayfa 3: Detay
detail = visual(24, 104, 1872, 928, "tableEx", {"Values": {"projections": [
    proj(col("Challenge", "YuklemeZamani"), "Yükleme zamanı"), proj(col("Challenge", "KayitID"), "Kayıt no"),
    proj(col("Kisiler", "Kisi"), "Kişi"), proj(col("Kisiler", "Email"), "E-posta"),
    proj(col("Kisiler", "Bolge"), "Bölge"), proj(col("Kisiler", "Yonetici"), "Yönetici"),
    proj(mea("Toplam TEU"), "TEU"),
]}}, objects={"columnHeaders": props(fontSize=10, fontColor=solid(TEXT2)),
              "grid": props(gridHorizontal=True, gridHorizontalColor=solid("#EDEBE9"), rowPadding=4, textSize=10)},
    container=title("Tüm girişler", size=12), z=9000, sort=[(col("Challenge", "YuklemeZamani"), "Descending")])
page("detay", "Detay", header("TEU Challenge · Detay", "Tüm TEU girişleri, en yeniden eskiye")
     + [detail, footer(13000)])

# Sayfa 4: Panel (konteyner gemisi arka planlı koyu tasarım)
# Gemi sahnesi, cam paneller, ikonlar ve sabit yazılar arka plan resminde (dashboard/mockup/teu-glass.html?bg);
# veriye bağlı her şey arka planı şeffaf Power BI görselleridir.
PANEL_BG = "TEU_Panel_Arkaplan.png"


def clear():
    return {"background": props(show=False), "border": props(show=False), "dropShadow": props(show=False),
            "title": props(show=False), "visualHeader": props(show=False)}


def text_card(x, y, w, h, measure, size, color, z, bold=False):
    return visual(x, y, w, h, "card", {"Values": {"projections": [proj(mea(measure))]}}, objects={
        "labels": props(fontSize=size, color=solid(color), fontFamily="Segoe UI Semibold" if bold else "Segoe UI"),
        "categoryLabels": props(show=False),
        "wordWrap": props(show=True),
    }, container=clear(), z=z)


def dark_axes(show_values=False):
    return {
        "categoryAxis": props(show=True, fontSize=9, labelColor=solid(LIGHT_2), showAxisTitle=False,
                              gridlineShow=False),
        "valueAxis": props(show=show_values, fontSize=9, labelColor=solid(LIGHT_2), showAxisTitle=False,
                           gridlineShow=False),
        "legend": props(show=False),
    }


def dark_chart(x, y, w, h, vtype, roles, z, extra=None, sort=None):
    objects = dark_axes()
    objects.update(extra or {})
    return visual(x, y, w, h, vtype, roles, objects=objects, container=clear(), z=z, sort=sort)


def measure_color(prop, color):
    return {"properties": {"fill": solid(color)}, "selector": {"metadata": f"_Olculer.{prop}"}}


panel = [
    text_card(560, 40, 800, 56, "Selamlama", 20, LIGHT, 100, bold=True),
    text_card(1712, 36, 176, 30, "Benim Adım", 13, LIGHT, 110, bold=True),
    text_card(1712, 64, 176, 26, "Benim Rolüm", 10, LIGHT_2, 120),
]
for i, (fld, x, w) in enumerate([(col("Tarih", "Donem"), 1082, 210), (col("Kisiler", "Bolge"), 1489, 96)]):
    panel.append(visual(x, 450, w, 48, "slicer", {"Values": {"projections": [proj(fld)]}}, objects={
        "data": props(mode="Dropdown"),
        "header": props(show=False),
        "items": props(fontColor=solid(LIGHT), background=solid("#1A1714"), textSize=11),
    }, container=clear(), z=200 + i))

# Satır 1: TEU'n, Sıran, Bugün
for i, (value, note, x) in enumerate([("Benim TEU", "Hedef Açıklama", 40), ("Sıram Metin", "Sıra Açıklama", 524),
                                      ("Bugün Benim TEU", "Bugün Açıklama", 1008)]):
    panel += [text_card(x + 8, 640, 200, 76, value, 34, LIGHT, 300 + i * 10, bold=True),
              text_card(x + 8, 716, 236, 52, note, 10, LIGHT_2, 301 + i * 10)]
panel.append(dark_chart(256, 600, 236, 168, "clusteredBarChart", {
    "Category": {"projections": [proj(col("Challenge", "KonteynerTipi"), "Konteyner tipi")]},
    "Y": {"projections": [proj(mea("Benim TEU"), "TEU")]},
}, 400, {"dataPoint": [{"properties": {"fill": solid(ACCENT)}}],
         "labels": props(show=True, color=solid(LIGHT), fontSize=9)},
    sort=[(mea("Benim TEU"), "Descending")]))
panel.append(dark_chart(748, 596, 228, 172, "lineChart", {
    "Category": {"projections": [proj(col("Tarih", "GunEtiket"), "Gün")]},
    "Y": {"projections": [proj(mea("Son 7 Gün Sen"), "Sen"), proj(mea("Son 7 Gün Öndeki"), "Bir öndeki")]},
}, 410, {"dataPoint": [measure_color("Son 7 Gün Sen", ACCENT), measure_color("Son 7 Gün Öndeki", LIGHT_2)],
         "lineStyles": props(strokeWidth=3, showMarker=False),
         "legend": props(show=True, position="Top", fontSize=9, labelColor=solid(LIGHT_2), showTitle=False),
         "valueAxis": props(show=True, fontSize=9, labelColor=solid(LIGHT_2), showAxisTitle=False,
                            gridlineShow=False)}))
panel.append(dark_chart(1240, 596, 220, 172, "clusteredColumnChart", {
    "Category": {"projections": [proj(col("Tarih", "GunEtiket"), "Gün")]},
    "Y": {"projections": [proj(mea("Son 7 Gün Benim TEU"), "TEU")]},
}, 420, {"dataPoint": [{"properties": {"fill": solid(ACCENT_2)}}],
         "labels": props(show=True, color=solid(LIGHT), fontSize=9)}))

# Satır 2: Hedefe kalan, Şirket yarışı
for x, big, line1, line2, left, right in [
    (40, "Hedefe Kalan TEU", "Üst Sıra Metin", "Haftalık Değişim", "Günlük Ortalama", "Gereken Tempo"),
    (766, "Toplam TEU", "Dönem Etiketi", "Şirket Alt Metin", "Lider Metin", "Lider Bölge Metin"),
]:
    panel += [
        text_card(x + 153, 812, 400, 58, big, 30, ACCENT, 500 + x, bold=True),
        text_card(x + 153, 868, 400, 28, line1, 12, LIGHT, 501 + x, bold=True),
        text_card(x + 153, 892, 400, 24, line2, 10, LIGHT_2, 502 + x),
        text_card(x + 12, 990, 240, 40, left, 16, LIGHT, 503 + x),
        text_card(x + 454, 990, 240, 40, right, 16, LIGHT, 504 + x),
    ]
panel.append(dark_chart(790, 916, 660, 52, "clusteredColumnChart", {
    "Category": {"projections": [proj(col("Tarih", "GunEtiket"), "Gün")]},
    "Y": {"projections": [proj(mea("Toplam TEU"), "Günlük TEU")]},
}, 600, {"dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": mea("Günlük Şirket Rengi")}}}},
                        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}],
         "categoryAxis": props(show=False), "valueAxis": props(show=False), "labels": props(show=False)}))

# Sağ kart: kişisel hedef göstergesi
panel += [
    text_card(1586, 556, 200, 30, "Hedef Etiketi", 11, LIGHT_2, 700),
    visual(1516, 596, 340, 230, "gauge", {
        "Y": {"projections": [proj(mea("Benim TEU"), "TEU")]},
        "MaxValue": {"projections": [proj(mea("Benim Hedef"), "Hedef")]},
    }, objects={"dataPoint": props(fill=solid(ACCENT)), "calloutValue": props(show=False),
                "labels": props(show=False)}, container=clear(), z=710),
    text_card(1586, 760, 200, 64, "Hedef Oranı", 36, LIGHT, 720, bold=True),
    text_card(1566, 846, 240, 30, "Hedef İlerleme Metin", 11, LIGHT_2, 730),
    text_card(1504, 990, 364, 36, "Bölge İçi Metin", 10, LIGHT_2, 740),
]
page("panel", "Panel", panel, image=PANEL_BG)

# ---------------------------------------------------------------- Proje dosyaları

THEME = {
    "name": "TEU Challenge",
    "dataColors": [ME, PRIMARY, DARK_GREY, CONTEXT, "#1BAF7A", "#6250D6", "#EDA100", "#E87BA4"],
    "background": "#FFFFFF", "foreground": TEXT, "tableAccent": PRIMARY,
    "good": "#107C10", "neutral": "#EDA100", "bad": "#C50F1F",
    "textClasses": {
        "callout": {"fontSize": 36, "fontFace": "Segoe UI Semibold", "color": TEXT},
        "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": TEXT},
        "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": TEXT},
        "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": TEXT2},
    },
    "visualStyles": {
        "*": {"*": {
            "background": [{"show": True, "color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
            "border": [{"show": True, "color": {"solid": {"color": "#E1DFDD"}}, "radius": 8}],
            "dropShadow": [{"show": True, "preset": "Custom", "position": "Outer", "color": {"solid": {"color": "#000000"}},
                            "transparency": 92, "shadowBlur": 6, "shadowDistance": 1, "shadowSpread": 0, "angle": 90}],
            "padding": [{"top": 12, "bottom": 12, "left": 16, "right": 16}],
            "title": [{"show": True, "fontSize": 12, "bold": True, "fontColor": {"solid": {"color": TEXT}}}],
        }},
        "page": {"*": {
            "background": [{"color": {"solid": {"color": CANVAS}}, "transparency": 0}],
            "outspace": [{"color": {"solid": {"color": CANVAS}}, "transparency": 0}],
        }},
    },
}

write(ROOT / f"{NAME}.pbip", {
    "$schema": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
    "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True},
})
for folder, kind in [(REPORT, "Report"), (MODEL, "SemanticModel")]:
    write(folder / ".platform", {
        "$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": kind, "displayName": NAME}, "config": {"version": "2.0", "logicalId": uid()},
    })
write(MODEL / "definition.pbism", {
    "$schema": f"{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json", "version": "4.0", "settings": {},
})
write(MODEL / "model.bim", model)
write(REPORT / "definition.pbir", {
    "$schema": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json", "version": "4.0",
    "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}},
})
write(REPORT / "definition" / "version.json", {
    "$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0",
})
write(REPORT / "definition" / "report.json", {
    "$schema": f"{SCHEMA}/item/report/definition/report/2.0.0/schema.json",
    "themeCollection": {"customTheme": {"name": "TEU_Tema.json", "reportVersionAtImport": "5.59",
                                        "type": "RegisteredResources"}},
    "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                          "items": [{"name": "TEU_Tema.json", "path": "TEU_Tema.json", "type": "CustomTheme"},
                                    {"name": PANEL_BG, "path": PANEL_BG, "type": "Image"}]}],
    "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                 "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                 "useEnhancedTooltips": True},
})
write(REPORT / "definition" / "pages" / "pages.json", {
    "$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": ["panel", "liderlik", "bolgeler", "detay"], "activePageName": "panel",
})
write(REPORT / "StaticResources" / "RegisteredResources" / "TEU_Tema.json", THEME)
shutil.copyfile(ROOT.parent / "mockup" / "teu-glass-bg.png", REPORT / "StaticResources" / "RegisteredResources" / PANEL_BG)
write(ROOT / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf")

print(f"{len(people)} kişi, {len(entries)} giriş · Can Demir: {final[3]} TEU, dün {rank(yesterday, 3)}. → bugün "
      f"{rank(final, 3)}.")
