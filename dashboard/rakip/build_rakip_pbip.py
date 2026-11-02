"""Rakip & Pazar Radarı Power BI projesini (.pbip) üretir.

Kullanım: python3 dashboard/rakip/build_rakip_pbip.py <ornek.xlsx> <çıktı-klasörü>

- Power Query, SharePoint klasöründeki haftalık dosyaları (W44.xlsx gibi) birleştirir; dosya adındaki hafta
  "Dosya haftası" olur. KaynakModu parametresi "Ornek" iken verilen Excel modele gömülü örnek olarak kullanılır.
- Örnek Excel modelin içine gömüldüğü için çıktı klasörünü herkese açık bir yere koymayın.
- Sayfa arka planı katmanlar/pbi-arkaplan.png'dir (katman_export.js üretir).
"""
import base64
import json
import random
import shutil
import sys
import uuid
from pathlib import Path

SRC_XLSX = Path(sys.argv[1])
OUT = Path(sys.argv[2])
HERE = Path(__file__).resolve().parent
NAME = "Rakip-Pazar-Radari"
REPORT, MODEL = OUT / f"{NAME}.Report", OUT / f"{NAME}.SemanticModel"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"
BG = "Radar_Arkaplan.png"
LAYOUT = json.loads((HERE / "katmanlar" / "katmanlar.json").read_text(encoding="utf-8"))
PANEL = {p["id"]: p for p in LAYOUT["panels"]}

rng = random.Random(45)
uid = lambda: str(uuid.UUID(int=rng.getrandbits(128), version=4))
hexid = lambda: "%020x" % rng.getrandbits(80)
ACC, ACC2, LIGHT, LIGHT2, LIGHT3, PANEL_BG = "#FF7A2F", "#F6B73C", "#F5F2EE", "#B3AFAB", "#7E7B78", "#1C1A18"


# ---------------------------------------------------------------- Yardımcılar
def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2)) + "\n",
                    encoding="utf-8")


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


def mea(prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Olculer"}}, "Property": prop}}


def proj(field, display=None):
    inner = field.get("Column") or field.get("Measure")
    entity, prop = inner["Expression"]["SourceRef"]["Entity"], inner["Property"]
    p = {"field": field, "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if display:
        p["displayName"] = display
    return p


def props(**kw):
    return [{"properties": {k: (v if isinstance(v, dict) else lit(v)) for k, v in kw.items()}}]


def clear():
    return {"background": props(show=False), "border": props(show=False), "dropShadow": props(show=False),
            "title": props(show=False), "visualHeader": props(show=False)}


def visual(x, y, w, h, vtype, query=None, objects=None, z=0, sort=None, container=None):
    v = {"visualType": vtype}
    if query:
        v["query"] = {"queryState": query}
        if sort:
            v["query"]["sortDefinition"] = {"sort": [{"field": f, "direction": d} for f, d in sort]}
    if objects:
        v["objects"] = objects
    v["visualContainerObjects"] = container or clear()
    v["drillFilterOtherVisuals"] = True
    return {"$schema": f"{SCHEMA}/item/report/definition/visualContainer/2.0.0/schema.json", "name": hexid(),
            "position": {"x": round(x), "y": round(y), "z": z, "height": round(h), "width": round(w), "tabOrder": z},
            "visual": v}


def textbox(x, y, w, h, paragraphs, z):
    """paragraphs: [(metin, punto, kalın, renk)]"""
    ps = [{"textRuns": [{"value": t, "textStyle": {"fontSize": f"{s}pt", "color": c, "fontFamily": "Segoe UI",
                                                   **({"fontWeight": "bold"} if b else {})}}],
           "horizontalTextAlignment": "left"} for t, s, b, c in paragraphs]
    return visual(x, y, w, h, "textbox", objects={"general": [{"properties": {"paragraphs": ps}}]}, z=z)


def text_card(x, y, w, h, measure, size, color, z, bold=False, align="left"):
    """Ölçüden gelen metin: dolgusu, çerçevesi ve ikonu kapalı düğme (sola hizalı, satır kaydırır)."""
    states = ["default", "hover", "press", "selected"]
    text = {"show": lit(True), "text": {"expr": mea(measure)}, "fontSize": lit(size), "fontColor": solid(color),
            "fontFamily": lit("Segoe UI Semibold" if bold else "Segoe UI"), "horizontalAlignment": lit(align),
            "verticalAlignment": lit("top"), "leftMargin": lit(0), "rightMargin": lit(0), "topMargin": lit(0),
            "bottomMargin": lit(0)}
    return visual(x, y, w, h, "actionButton", objects={
        "text": [{"properties": text, "selector": {"id": st}} for st in states],
        "fill": [{"properties": {"show": lit(False)}, "selector": {"id": st}} for st in states],
        "outline": [{"properties": {"show": lit(False)}, "selector": {"id": st}} for st in states],
        "icon": [{"properties": {"show": lit(False)}, "selector": {"id": st}} for st in states],
        "shadow": props(show=False), "glow": props(show=False),
    }, z=z)


def dark_table(x, y, w, h, columns, z, sort=None, widths=None, font=11, image=None):
    """widths: sütun başına piksel genişlik (sırasıyla); image: (genişlik, yükseklik) SVG/resim sütunları için."""
    objects = {
        "columnHeaders": props(fontColor=solid(LIGHT3), backColor=solid(PANEL_BG), fontSize=font - 1, outlineStyle=0,
                               autoSizeColumnWidth=False, wordWrap=False),
        "values": props(fontColorPrimary=solid(LIGHT), fontColorSecondary=solid(LIGHT), backColorPrimary=solid(PANEL_BG),
                        backColorSecondary=solid(PANEL_BG), fontSize=font, outlineStyle=0, wordWrap=False),
        "grid": props(gridHorizontal=True, gridHorizontalColor=solid("#2E2B28"), gridVertical=False, rowPadding=2,
                      outlineColor=solid(PANEL_BG), textSize=font),
        "total": props(totals=False),
    }
    if image:
        objects["grid"][0]["properties"].update(imageWidth=lit(image[0]), imageHeight=lit(image[1]))
    if widths:
        objects["columnWidth"] = [{"properties": {"value": lit(wd)}, "selector": {"metadata": c["queryRef"]}}
                                  for c, wd in zip(columns, widths)]
    return visual(x, y, w, h, "tableEx", {"Values": {"projections": columns}}, objects=objects, z=z, sort=sort)


def dark_axes():
    return {"categoryAxis": props(show=True, fontSize=9, labelColor=solid(LIGHT2), showAxisTitle=False, gridlineShow=False),
            "valueAxis": props(show=False, gridlineShow=False, showAxisTitle=False),
            "labels": props(show=True, color=solid(LIGHT), fontSize=10, labelDisplayUnits=1, labelPrecision=0)}


# ---------------------------------------------------------------- Power Query
xlsx_b64 = base64.b64encode(SRC_XLSX.read_bytes()).decode()
chunks = [xlsx_b64[i:i + 2000] for i in range(0, len(xlsx_b64), 2000)]
M_ORNEK = "let\n    // Örnek dosya (KaynakModu = \"Ornek\" iken kullanılır)\n    Veri = Binary.FromText(\n        " + \
          "\n        & ".join(f'"{c}"' for c in chunks) + ",\n        BinaryEncoding.Base64)\nin\n    Veri"

PARAMS = {
    "KaynakModu": ('"Ornek" meta [IsParameterQuery = true, List = {"Ornek", "SharePoint"}, DefaultValue = "Ornek", '
                   'Type = "Text", IsParameterQueryRequired = true]'),
    "SharePointSite": ('"https://SIRKETINIZ.sharepoint.com/sites/SITE-ADI" meta [IsParameterQuery = true, '
                       'Type = "Text", IsParameterQueryRequired = true]'),
    "SharePointKlasor": '"Rakip ve Pazar" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]',
}
EXPRESSIONS = {
    "OrnekDosya": M_ORNEK,
    "KurTablosu": """
let
    // 1 birim = kaç USD. Gerçek kurları buraya yazın (ya da bir kur kaynağına bağlayın).
    Kaynak = #table(type table [PB = text, KurUSD = number], {{"USD", 1}, {"EUR", 1}, {"GBP", 1}})
in
    Kaynak""",
    "RakipEsleme": """
let
    // Aynı rakibin farklı yazımları → tek ad. Yeni yazım farkı çıkarsa satır ekleyin.
    Kaynak = #table(type table [Kaynak = text, Hedef = text], {
        {"CULINES", "CUL LINES"}, {"NCA (NORHT CAPE AGENCY)", "NCA"}, {"HIKARU (FEVZI GANDUR)", "HIKARU"}})
in
    Kaynak""",
    "fnTemizMetin": """
(v as any) as any =>
    if v is text then
        let
            t = Text.Combine(List.Select(Text.Split(Text.Clean(Text.Replace(v, "#(00A0)", " ")), " "), each _ <> ""), " ")
        in
            if t = "" then null else t
    else v""",
    "fnSayi": """
// Sayı, "2150 - 2350" gibi aralık (orta nokta) veya Excel'in tarihe çevirdiği "8-9" → sayı; "Kapalı", "-" → null
(v as any) as nullable number =>
    if v = null then null
    else if v is number then v
    else if v is date or v is datetime then (Date.Day(v) + Date.Month(v)) / 2
    else
        let
            Parcalar = Text.SplitAny(Text.From(v), " -–/~"),
            Sayilar = List.RemoveNulls(List.Transform(Parcalar, each try Number.FromText(_, "en-US") otherwise null))
        in
            if List.IsEmpty(Sayilar) then null else List.Average(Sayilar)""",
    "fnRakip": """
(v as any) as nullable text =>
    let
        Ad = if v = null then null else Text.Upper(fnTemizMetin(Text.From(v))),
        Eslesen = Table.SelectRows(RakipEsleme, each [Kaynak] = Ad)
    in
        if Ad = null or Table.IsEmpty(Eslesen) then Ad else Eslesen{0}[Hedef]""",
    "fnSayfa": """
// Sayfadaki başlık satırını (ilk sütunu ilkBaslik olan satır) bulup tabloyu ondan başlatır
(icerik as binary, sayfa as text, ilkBaslik as text) as table =>
    let
        Kitap = Excel.Workbook(icerik, null, true),
        Veri = Kitap{[Item = sayfa, Kind = "Sheet"]}[Data],
        Ilk = List.Transform(Table.Column(Veri, "Column1"), each if _ is text then Text.Trim(_) else _),
        Atla = Table.Skip(Veri, List.PositionOf(Ilk, ilkBaslik)),
        Baslik = Table.PromoteHeaders(Atla, [PromoteAllScalars = true]),
        Dolu = Table.SelectRows(Baslik, each List.NonNullCount(Record.FieldValues(_)) > 1)
    in
        Dolu""",
    "DosyaListesi": """
let
    Kaynak =
        if KaynakModu = "SharePoint" then
            let
                Tum = SharePoint.Files(SharePointSite, [ApiVersion = 15]),
                Klasor = Table.SelectRows(Tum, each Text.Contains([Folder Path], SharePointKlasor)
                    and Text.Lower([Extension]) = ".xlsx" and not Text.StartsWith([Name], "~")),
                Sec = Table.SelectColumns(Klasor, {"Name", "Content", "Date modified"})
            in
                Sec
        else
            #table(type table [Name = text, Content = binary, #"Date modified" = datetime],
                {{"W45.xlsx", OrnekDosya, #datetime(2026, 11, 2, 9, 0, 0)}}),
    // Dosya adı W44.xlsx biçiminde olmalı: içindeki sayı dosya haftasıdır
    Hafta = Table.AddColumn(Kaynak, "DosyaHaftasi", each Number.From(Text.Select([Name], {"0".."9"})), Int64.Type),
    Yil = Table.AddColumn(Hafta, "DosyaYili", each Date.Year([Date modified]), Int64.Type),
    Sira = Table.AddColumn(Yil, "DosyaSira", each [DosyaYili] * 100 + [DosyaHaftasi], Int64.Type)
in
    Sira""",
}


def fact(sheet, first, cols, extra):
    """Tüm dosyalardan bir sayfayı birleştirir; cols: (Excel başlığı, yeni ad)."""
    src = "{" + ", ".join(f'"{a}"' for a, _ in cols) + "}"
    dst = "{" + ", ".join(f'"{b}"' for _, b in cols) + "}"
    return f"""
let
    Dosyalar = Table.SelectColumns(DosyaListesi, {{"DosyaHaftasi", "DosyaSira", "Content"}}),
    Sayfa = Table.AddColumn(Dosyalar, "Veri", each fnSayfa([Content], "{sheet}", "{first}")),
    Ac = Table.ExpandTableColumn(Table.RemoveColumns(Sayfa, {{"Content"}}), "Veri", {src}, {dst}),
    Temiz = Table.TransformColumns(Ac, {{}}, fnTemizMetin),
{extra}"""


M_NAVLUN = fact("Rakip Navlun", "Hafta", [
    ("Hafta", "Hafta"), ("Turkon İlgili Servis", "Servis"), ("Rakip", "Rakip"), ("POL", "POL"), ("POD", "POD"),
    ("PB", "PB"), ("20'", "Ham20"), ("40'", "Ham40"), ("Free Time", "FreeTime"), ("Fiyatlama Türü", "FiyatlamaTuru"),
    ("Direkt/Aktarmalı", "Aktarma"), ("Aktarma Limanı", "AktarmaLimani"), ("TT", "HamTT"),
    ("Yetersiz Ekipman", "YetersizEkipman"), ("Yük Durumu", "YukDurumu"), ("Notlar", "Notlar"),
    ("Servis Durumu", "ServisDurumu"), ("Bölge", "Bolge"), ("Eklenecek Kalemler", "EklenecekKalemler")], """\
    Rakip = Table.TransformColumns(Temiz, {{"Rakip", fnRakip, type text}}),
    Yuk = Table.TransformColumns(Rakip, {{"YukDurumu", each if _ is text and Text.Lower(_) = "sold out" then "Overbooked" else _, type text}}),
    F20 = Table.AddColumn(Yuk, "Fiyat20", each fnSayi([Ham20]), type number),
    F40 = Table.AddColumn(F20, "Fiyat40", each fnSayi([Ham40]), type number),
    TT = Table.AddColumn(F40, "TTGun", each fnSayi([HamTT]), type number),
    Kapali = Table.AddColumn(TT, "Kapali", each List.AnyTrue(List.Transform({[Ham20], [Ham40]},
        each _ is text and List.Contains({"kapalı", "yok"}, Text.Lower(_)))), type logical),
    Kur = Table.NestedJoin(Kapali, {"PB"}, KurTablosu, {"PB"}, "K", JoinKind.LeftOuter),
    KurAc = Table.ExpandTableColumn(Kur, "K", {"KurUSD"}),
    Usd20 = Table.AddColumn(KurAc, "Fiyat20USD", each if [Fiyat20] = null then null
        else [Fiyat20] * (if [KurUSD] = null then 1 else [KurUSD]), type number),
    Usd40 = Table.AddColumn(Usd20, "Fiyat40USD", each if [Fiyat40] = null then null
        else [Fiyat40] * (if [KurUSD] = null then 1 else [KurUSD]), type number),
    HaftaSayi = Table.TransformColumns(Usd40, {{"Hafta", Number.From, Int64.Type}, {"FreeTime", fnSayi, type number}}),
    Guncel = Table.AddColumn(HaftaSayi, "GuncelMi", each [Hafta] >= [DosyaHaftasi] - 1, type logical),
    BuHafta = Table.AddColumn(Guncel, "BuHaftaMi", each [Hafta] = [DosyaHaftasi], type logical),
    Metin = Table.TransformColumns(BuHafta, {{"Ham20", each if _ = null then null else Text.From(_), type text},
        {"Ham40", each if _ = null then null else Text.From(_), type text},
        {"HamTT", each if _ = null then null else Text.From(_), type text}}),
    No = Table.AddIndexColumn(Metin, "KayitNo", 1, 1, Int64.Type),
    Tipli = Table.TransformColumnTypes(No, {{"Servis", type text}, {"POL", type text}, {"POD", type text},
        {"PB", type text}, {"FiyatlamaTuru", type text}, {"Aktarma", type text}, {"AktarmaLimani", type text},
        {"YetersizEkipman", type text}, {"Notlar", type text}, {"ServisDurumu", type text}, {"Bolge", type text},
        {"EklenecekKalemler", type text}, {"KurUSD", type number}})
in
    Tipli""")

M_GEMI = fact("Gemi Takibi", "Hafta", [
    ("Hafta", "Hafta"), ("Turkon İlgili Servis", "Servis"), ("Bölge", "Bolge"), ("Rakip", "Rakip"),
    ("Gemi Adı", "GemiAdi"), ("Cut Off", "CutOff"), ("Rakip Servis Adı", "RakipServisAdi"),
    ("Direkt/Aktarmalı", "Aktarma"), ("Aktarma Limanı", "AktarmaLimani"), ("Durum", "Durum")], """\
    Rakip = Table.TransformColumns(Temiz, {{"Rakip", fnRakip, type text},
        {"Aktarma", each if _ = "DİREKT" then "Direkt" else _, type text},
        {"Hafta", Number.From, Int64.Type},
        {"CutOff", each try Date.From(_) otherwise null, type date}}),
    No = Table.AddIndexColumn(Rakip, "KayitNo", 1, 1, Int64.Type),
    Tipli = Table.TransformColumnTypes(No, {{"Servis", type text}, {"Bolge", type text}, {"GemiAdi", type text},
        {"RakipServisAdi", type text}, {"AktarmaLimani", type text}, {"Durum", type text}})
in
    Tipli""")

M_ARTIS = fact("Genel Fiyat Artışları", "Hafta", [
    ("Hafta", "Hafta"), ("Turkon ilgili Servis", "Servis"), ("Rakip", "Rakip"), ("Liman veya Ülke", "LimanUlke"),
    ("Artış Adı", "ArtisAdi"), ("20'", "Artis20"), ("40'", "Artis40"), ("Planlanan Başlangıç Tarihi", "Planlanan"),
    ("Ertelenen Tarih", "Ertelenen"), ("Durum", "Durum"), ("Açıklama", "Aciklama"),
    ("Son Güncelleyen Kişi", "Guncelleyen")], """\
    Rakip = Table.TransformColumns(Temiz, {{"Rakip", fnRakip, type text},
        {"Hafta", Number.From, Int64.Type}, {"Artis20", fnSayi, type number}, {"Artis40", fnSayi, type number},
        {"Planlanan", each try Date.From(_) otherwise null, type date},
        {"Ertelenen", each try Date.From(_) otherwise null, type date},
        {"Durum", each if _ = null then "Planlandı" else _, type text}}),
    Gecerli = Table.AddColumn(Rakip, "GecerliTarih", each if [Ertelenen] <> null then [Ertelenen] else [Planlanan], type date),
    No = Table.AddIndexColumn(Gecerli, "KayitNo", 1, 1, Int64.Type),
    Tipli = Table.TransformColumnTypes(No, {{"Servis", type text}, {"LimanUlke", type text}, {"ArtisAdi", type text},
        {"Aciklama", type text}, {"Guncelleyen", type text}})
in
    Tipli""")

M_PIYASA = fact("Piyasa Bilgisi", "Veri Giriş Tarihi", [
    ("Veri Giriş Tarihi", "Tarih"), ("Turkon ilgili Servis", "Servis"), ("Bölge", "Bolge"), ("Rakip", "Rakip"),
    ("Kategori", "Kategori"), ("Liman veya Ülke", "LimanUlke"), ("Açıklama", "Aciklama")], """\
    Rakip = Table.TransformColumns(Temiz, {{"Rakip", fnRakip, type text},
        {"Tarih", each try Date.From(_) otherwise null, type date}}),
    No = Table.AddIndexColumn(Rakip, "KayitNo", 1, 1, Int64.Type),
    Tipli = Table.TransformColumnTypes(No, {{"Servis", type text}, {"Bolge", type text}, {"Kategori", type text},
        {"LimanUlke", type text}, {"Aciklama", type text}})
in
    Tipli""")

M_SAHA = """
let
    // Piyasa notları + gemi takibindeki sefer aksaklıkları tek akışta
    Notlar = Table.SelectColumns(Table.AddColumn(Table.AddColumn(PiyasaBilgisi, "Tur", each "Not"), "Etiket", each [LimanUlke]),
        {"DosyaSira", "Servis", "Tarih", "Tur", "Rakip", "Aciklama", "Etiket"}),
    Aks = Table.SelectRows(GemiTakibi, each [Durum] <> null),
    Sefer = Table.SelectColumns(Table.RenameColumns(Table.AddColumn(Table.AddColumn(Aks, "Tur", each "Sefer"),
        "Detay", each Text.Combine(List.Select({[GemiAdi], "Hafta " & Text.From([Hafta])}, each _ <> null), " · ")),
        {{"CutOff", "Tarih"}, {"Durum", "Etiket"}}), {"DosyaSira", "Servis", "Tarih", "Tur", "Rakip", "Detay", "Etiket"}),
    SeferAd = Table.RenameColumns(Sefer, {{"Detay", "Aciklama"}}),
    Birlesik = Table.Combine({Notlar, SeferAd}),
    No = Table.AddIndexColumn(Birlesik, "KayitNo", 1, 1, Int64.Type),
    Tipli = Table.TransformColumnTypes(No, {{"Tarih", type date}, {"Tur", type text}, {"Rakip", type text},
        {"Aciklama", type text}, {"Etiket", type text}, {"Servis", type text}})
in
    Tipli"""
M_DOSYALAR = """
let
    Kaynak = Table.SelectColumns(DosyaListesi, {"DosyaSira", "DosyaHaftasi", "DosyaYili"}),
    Tekil = Table.Distinct(Kaynak, {"DosyaSira"}),
    Etiket = Table.AddColumn(Tekil, "Hafta", each "Hafta " & Text.From([DosyaHaftasi]) & " · " & Text.From([DosyaYili]), type text)
in
    Etiket"""
M_SERVIS = """
let
    Liste = List.Distinct(List.RemoveNulls(List.Combine({RakipNavlun[Servis], GemiTakibi[Servis],
        FiyatArtislari[Servis], PiyasaBilgisi[Servis]}))),
    Tablo = Table.FromList(List.Sort(Liste), Splitter.SplitByNothing(), type table [Servis = text])
in
    Tablo"""
M_OLCULER = "let\n    Kaynak = #table(type table [Gizli = text], {})\nin\n    Kaynak"

# ---------------------------------------------------------------- DAX ölçüleri
S = "VAR s = [Seçili Dosya]\n"  # seçili haftanın dosyası (dilimleyici boşsa en son dosya)


def at_file(expr):
    return S + f"RETURN CALCULATE ( {expr}, Dosyalar[DosyaSira] = s )"


MEASURES = [
    ("Seçili Dosya", "MAX ( Dosyalar[DosyaSira] )", "0", "Seçili hafta dosyası; dilimleyici boşsa en son dosya."),
    ("Seçili Hafta", "VAR s = [Seçili Dosya]\nRETURN LOOKUPVALUE ( Dosyalar[DosyaHaftasi], Dosyalar[DosyaSira], s )", "0", None),
    ("Kayıt Sayısı", at_file("COUNTROWS ( RakipNavlun )"), "#,0", None),
    ("Rakip Sayısı", at_file("DISTINCTCOUNT ( RakipNavlun[Rakip] )"), "0", None),
    ("Rota Sayısı", at_file("COUNTROWS ( SUMMARIZE ( RakipNavlun, RakipNavlun[POL], RakipNavlun[POD] ) )"), "0", None),
    ("Güncel Kayıt", at_file("COUNTROWS ( FILTER ( RakipNavlun, RakipNavlun[GuncelMi] ) )"), "#,0", None),
    ("Bu Hafta Kayıt", at_file("COUNTROWS ( FILTER ( RakipNavlun, RakipNavlun[BuHaftaMi] ) )"), "#,0", None),
    ("Güncel Oran", "DIVIDE ( [Güncel Kayıt], [Kayıt Sayısı] )", "0%", "Son 2 haftada güncellenen fiyat kaydı oranı."),
    ("Yük Arıyor", at_file('COUNTROWS ( FILTER ( RakipNavlun, RakipNavlun[YukDurumu] = "Yük Arıyor/Yerini Dolduramıyor" ) )') ,
     "#,0", None),
    ("Overbooked", at_file('COUNTROWS ( FILTER ( RakipNavlun, RakipNavlun[YukDurumu] = "Overbooked" ) )'), "#,0", None),
    ("Yük Arıyor %", "DIVIDE ( [Yük Arıyor], [Kayıt Sayısı] )", "0%", None),
    ("Ekipman", at_file("COUNTROWS ( FILTER ( RakipNavlun, NOT ISBLANK ( RakipNavlun[YetersizEkipman] ) ) )"), "#,0", None),
    ("Ekipman 20", at_file('COUNTROWS ( FILTER ( RakipNavlun, CONTAINSSTRING ( RakipNavlun[YetersizEkipman], "20" ) ) )'),
     "#,0", None),
    ("Ekipman %", "DIVIDE ( [Ekipman], [Kayıt Sayısı] )", "0%", None),
    ("TT Direkt", at_file('MEDIANX ( FILTER ( RakipNavlun, RakipNavlun[Aktarma] = "Direkt" && NOT ISBLANK ( RakipNavlun[TTGun] ) ), RakipNavlun[TTGun] )'),
     "0.0", None),
    ("TT Aktarmalı", at_file('MEDIANX ( FILTER ( RakipNavlun, RakipNavlun[Aktarma] = "Aktarmalı" && NOT ISBLANK ( RakipNavlun[TTGun] ) ), RakipNavlun[TTGun] )'),
     "0.0", None),
    ("TT Farkı", "[TT Aktarmalı] - [TT Direkt]", '0" gün"', "Aktarmalı servislerin direkte göre medyan fazladan transit süresi."),
    ("Direkt Prim", S + """RETURN
    CALCULATE (
        MEDIANX (
            FILTER (
                ADDCOLUMNS (
                    VALUES ( RakipNavlun[POD] ),
                    "@d", CALCULATE ( MEDIAN ( RakipNavlun[Fiyat40USD] ), RakipNavlun[Aktarma] = "Direkt" ),
                    "@a", CALCULATE ( MEDIAN ( RakipNavlun[Fiyat40USD] ), RakipNavlun[Aktarma] = "Aktarmalı" ),
                    "@nd", CALCULATE ( COUNT ( RakipNavlun[Fiyat40USD] ), RakipNavlun[Aktarma] = "Direkt" ),
                    "@na", CALCULATE ( COUNT ( RakipNavlun[Fiyat40USD] ), RakipNavlun[Aktarma] = "Aktarmalı" )
                ),
                [@nd] >= 2 && [@na] >= 2
            ),
            DIVIDE ( [@d], [@a] ) - 1
        ),
        Dosyalar[DosyaSira] = s
    )""", "+0%;-0%;0%", "Aynı POD'da direkt servisin aktarmalıya göre medyan 40' fiyat farkı."),
    ("Gözlem 40", at_file("COUNT ( RakipNavlun[Fiyat40USD] )"), "0", None),
    ("Min 40", at_file("MIN ( RakipNavlun[Fiyat40USD] )"), "#,0", None),
    ("Medyan 40", at_file("MEDIAN ( RakipNavlun[Fiyat40USD] )"), "#,0", None),
    ("Max 40", at_file("MAX ( RakipNavlun[Fiyat40USD] )"), "#,0", None),
    ("En Ucuz Rakip", S + """VAR mn = [Min 40]
RETURN
    CALCULATE (
        CONCATENATEX (
            TOPN ( 1, FILTER ( VALUES ( RakipNavlun[Rakip] ), CALCULATE ( MIN ( RakipNavlun[Fiyat40USD] ) ) = mn ),
                RakipNavlun[Rakip], ASC ),
            RakipNavlun[Rakip]
        ),
        Dosyalar[DosyaSira] = s
    )""", None, None),
    ("Rota Sırası", """IF (
    ISINSCOPE ( RakipNavlun[POD] ),
    RANKX ( ALLSELECTED ( RakipNavlun[Servis], RakipNavlun[POD] ), [Gözlem 40], , DESC, SKIP )
)""", "0", None),
    ("Koridorda", "[Rota Sırası] <= 8 && [Gözlem 40] >= 3", None, "En çok fiyat girilen 8 rota (en az 3 gözlem)."),
    ("K Gözlem", "IF ( [Koridorda], [Gözlem 40] )", "0", None),
    ("K Min", "IF ( [Koridorda], [Min 40] )", "#,0", None),
    ("K Medyan", "IF ( [Koridorda], [Medyan 40] )", "#,0", None),
    ("K Max", "IF ( [Koridorda], [Max 40] )", "#,0", None),
    ("K En Ucuz", "IF ( [Koridorda], [En Ucuz Rakip] )", None, None),
    ("K Aralık", """VAR mn = [K Min]
VAR mx = [K Max]
VAR md = [K Medyan]
VAR W = 330
VAR pos = ROUND ( DIVIDE ( md - mn, mx - mn, 0 ) * W, 0 )
VAR lbl = "font-family='Segoe UI' font-size='12' fill='%23B3AFAB'"
RETURN
    IF (
        NOT ISBLANK ( md ),
        "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='460' height='18'>"
            & "<text x='0' y='13' " & lbl & ">" & FORMAT ( mn, "0" ) & "</text>"
            & "<rect x='52' y='7' width='" & W & "' height='4' rx='2' fill='%23FFFFFF' fill-opacity='0.16'/>"
            & "<rect x='52' y='7' width='" & pos & "' height='4' rx='2' fill='%23FF7A2F'/>"
            & "<circle cx='" & 52 + pos & "' cy='9' r='6' fill='%23FFFFFF' stroke='%23FF7A2F' stroke-width='2.5'/>"
            & "<text x='" & 52 + W + 10 & "' y='13' " & lbl & ">" & FORMAT ( mx, "0" ) & "</text></svg>"
    )""", None, "Satırın kendi en düşük–en yüksek aralığında medyanın konumu (tablo resim sütunu)."),
    ("USEC Medyan 40", 'CALCULATE ( [Medyan 40], RakipNavlun[POD] = "USEC" )', "#,0", None),
    ("USEC Min", 'CALCULATE ( [Min 40], RakipNavlun[POD] = "USEC" )', "#,0", None),
    ("USEC En Ucuz", 'CALCULATE ( [En Ucuz Rakip], RakipNavlun[POD] = "USEC" )', None, None),
    ("USEC Renk", """VAR v = [USEC Medyan 40]
VAR mn = MINX ( ALLSELECTED ( RakipNavlun[Rakip] ), [USEC Medyan 40] )
RETURN IF ( v = mn, "%s", "#6E6A66" )""" % ACC, None, None),
    ("Artış 20", at_file("SUM ( FiyatArtislari[Artis20] )"), "+#,0", None),
    ("Artış 40", at_file("SUM ( FiyatArtislari[Artis40] )"), "+#,0", None),
    ("Artış Sayısı", at_file("COUNTROWS ( FiyatArtislari )"), "0", None),
    ("Ertelenen Artış", at_file('COUNTROWS ( FILTER ( FiyatArtislari, FiyatArtislari[Durum] = "Ertelendi" ) )'), "0", None),
    ("Saha Kaydı", at_file("COUNTROWS ( SahaNotlari )"), "0", None),
    # --- Metinler (başlık ve kart altları)
    ("Hafta Etiketi", '"HAFTA " & [Seçili Hafta] & " · PAZAR ÖZETİ"', None, None),
    ("Başlık", """VAR o = [Yük Arıyor %]
VAR durum = IF ( o >= 0.2, "Pazar yumuşak", IF ( o >= 0.1, "Pazar dengeli", "Pazar sıkı" ) )
RETURN durum & ": rakip kayıtlarında ""yük arıyor"" oranı %" & FORMAT ( o * 100, "0" )""", None,
     "Eşikler: %20 ve üzeri yumuşak, %10–20 dengeli, altı sıkı."),
    ("Özet Notu", """"20' ekipman açığı " & FORMAT ( [Ekipman 20], "0" ) & " kayıtta bildirildi · USEC'te en ucuz 40' "
    & [USEC En Ucuz] & " " & FORMAT ( [USEC Min], "#,0" ) & " USD · aktarmalı servisler "
    & FORMAT ( [TT Farkı], "0" ) & " gün daha yavaş\"""", None, None),
    ("K1 Alt", 'FORMAT ( [Kayıt Sayısı], "#,0" ) & " fiyat kaydı · " & [Rota Sayısı] & " POL–POD rotası"', None, None),
    ("K2 Alt", '"Son 2 haftada güncellenen · bu hafta " & FORMAT ( [Bu Hafta Kayıt], "0" ) & " kayıt"', None, None),
    ("K3 Alt", '"Fiyat kayıtlarının %" & FORMAT ( [Yük Arıyor %] * 100, "0" ) & " · " & FORMAT ( [Overbooked], "0" ) & " overbooked"',
     None, None),
    ("K4 Alt", "FORMAT ( [Ekipman 20], \"0\" ) & \" tanesi 20' · rakip yük alamıyor\"", None, None),
    ("K5 Alt", '"Medyan TT " & FORMAT ( [TT Direkt], "0" ) & " / " & FORMAT ( [TT Aktarmalı], "0" ) & " gün · fiyat farkı " & FORMAT ( [Direkt Prim], "+0%;-0%;0%" )',
     None, None),
    ("Artış Alt", '"Toplam " & FORMAT ( [Artış Sayısı], "0" ) & " duyuru · " & FORMAT ( [Ertelenen Artış], "0" ) & " ertelendi"',
     None, None),
    ("Altbilgi Sağ", '"Hafta " & [Seçili Hafta] & " verisi · " & FORMAT ( [Kayıt Sayısı], "#,0" ) & " rakip fiyat kaydı"', None, None),
]


def m_lines(t):
    return t.strip("\n").split("\n")


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


def table(name, cols, m, measures=None, hidden=False):
    t = {"name": name, "lineageTag": uid(), "columns": cols,
         "partitions": [{"name": name, "mode": "import", "source": {"type": "m", "expression": m_lines(m)}}]}
    if measures:
        t["measures"] = measures
    if hidden:
        t["isHidden"] = True
    return t


txt = lambda n, **k: column(n, "string", **k)
num = lambda n, fmt="#,0", **k: column(n, "double", fmt, **k)
i64 = lambda n, fmt="0", **k: column(n, "int64", fmt, **k)
dat = lambda n, **k: column(n, "dateTime", "dd.MM.yyyy", date_only=True, **k)
lgc = lambda n, **k: column(n, "boolean", **k)
FILE_COLS = lambda: [i64("DosyaHaftasi", hidden=True), i64("DosyaSira", hidden=True)]

measures = []
for name, dax, fmt, desc in MEASURES:
    m = {"name": name, "expression": m_lines(dax) if "\n" in dax.strip() else dax.strip(), "lineageTag": uid()}
    if fmt:
        m["formatString"] = fmt
    if desc:
        m["description"] = desc
    if name == "K Aralık":
        m["dataCategory"] = "ImageUrl"
    measures.append(m)

expressions = [{"name": n, "kind": "m", "expression": e, "lineageTag": uid(),
                "annotations": [{"name": "PBI_ResultType", "value": "Text"}]} for n, e in PARAMS.items()]
expressions += [{"name": n, "kind": "m", "expression": m_lines(e), "lineageTag": uid()} for n, e in EXPRESSIONS.items()]

tables = [
    table("_Olculer", [txt("Gizli", hidden=True)], M_OLCULER, measures),
    table("Dosyalar", [i64("DosyaSira", hidden=True), i64("DosyaHaftasi"), i64("DosyaYili"),
                       txt("Hafta", sort_by="DosyaSira")], M_DOSYALAR),
    table("Servisler", [txt("Servis")], M_SERVIS),
    table("RakipNavlun", FILE_COLS() + [
        i64("Hafta"), txt("Servis"), txt("Rakip"), txt("POL"), txt("POD"), txt("PB"), txt("Ham20"), txt("Ham40"),
        num("FreeTime", "0"), txt("FiyatlamaTuru"), txt("Aktarma"), txt("AktarmaLimani"), txt("HamTT"),
        txt("YetersizEkipman"), txt("YukDurumu"), txt("Notlar"), txt("ServisDurumu"), txt("Bolge"),
        txt("EklenecekKalemler"), num("Fiyat20"), num("Fiyat40"), num("TTGun", "0.0"), lgc("Kapali"),
        num("KurUSD", "0.0000", hidden=True), num("Fiyat20USD"), num("Fiyat40USD"), lgc("GuncelMi"), lgc("BuHaftaMi"),
        i64("KayitNo")], M_NAVLUN),
    table("GemiTakibi", FILE_COLS() + [
        i64("Hafta"), txt("Servis"), txt("Bolge"), txt("Rakip"), txt("GemiAdi"), dat("CutOff"), txt("RakipServisAdi"),
        txt("Aktarma"), txt("AktarmaLimani"), txt("Durum"), i64("KayitNo")], M_GEMI),
    table("FiyatArtislari", FILE_COLS() + [
        i64("Hafta"), txt("Servis"), txt("Rakip"), txt("LimanUlke"), txt("ArtisAdi"), num("Artis20"), num("Artis40"),
        dat("Planlanan"), dat("Ertelenen"), txt("Durum"), txt("Aciklama"), txt("Guncelleyen"), dat("GecerliTarih"),
        i64("KayitNo")], M_ARTIS),
    table("PiyasaBilgisi", FILE_COLS() + [
        dat("Tarih"), txt("Servis"), txt("Bolge"), txt("Rakip"), txt("Kategori"), txt("LimanUlke"), txt("Aciklama"),
        i64("KayitNo")], M_PIYASA),
    table("SahaNotlari", [i64("DosyaSira", hidden=True), txt("Servis"), dat("Tarih"), txt("Tur"), txt("Rakip"),
                          txt("Aciklama"), txt("Etiket"), i64("KayitNo")], M_SAHA),
]
rels = []
for t in ["RakipNavlun", "GemiTakibi", "FiyatArtislari", "PiyasaBilgisi", "SahaNotlari"]:
    rels.append({"name": uid(), "fromTable": t, "fromColumn": "DosyaSira", "toTable": "Dosyalar", "toColumn": "DosyaSira"})
    rels.append({"name": uid(), "fromTable": t, "fromColumn": "Servis", "toTable": "Servisler", "toColumn": "Servis"})

model = {"compatibilityLevel": 1567, "model": {
    "culture": "tr-TR", "sourceQueryCulture": "tr-TR", "defaultPowerBIDataSourceVersion": "powerBI_V3",
    "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
    "expressions": expressions, "tables": tables, "relationships": rels,
    "annotations": [{"name": "__PBI_TimeIntelligenceEnabled", "value": "0"}],
}}

# ---------------------------------------------------------------- Rapor
z = iter(range(1000, 100000, 100))
def slicers(y):
    """Servis: yatay çipler (tasarımdaki gibi); Hafta: koyu açılır liste, tek seçim, en yeni hafta en üstte."""
    items = props(fontColor=solid(LIGHT2), background=solid(PANEL_BG), textSize=11, outlineStyle=0)
    servis = visual(1040, y, 620, 44, "slicer", {"Values": {"projections": [proj(col("Servisler", "Servis"))]}}, objects={
        "data": props(mode="Basic"), "general": props(orientation=1, outlineColor=solid(PANEL_BG), outlineWeight=0),
        "header": props(show=False), "items": items, "selection": props(singleSelect=False, selectAllCheckboxEnabled=False),
    }, z=next(z))
    hafta = visual(1676, y, 204, 44, "slicer", {"Values": {"projections": [proj(col("Dosyalar", "Hafta"))]}}, objects={
        "data": props(mode="Dropdown"), "header": props(show=False), "items": items,
        "dropdown": props(borderColor=solid("#3A3633"), borderRadius=20, iconColor=solid(LIGHT2)),
        "general": props(outlineColor=solid(PANEL_BG), outlineWeight=0),
        "selection": props(singleSelect=True),
    }, z=next(z), sort=[(col("Dosyalar", "Hafta"), "Descending")])
    return [servis, hafta]


radar = [textbox(108, 32, 420, 56, [("Rakip & Pazar Radarı", 14, True, LIGHT),
                                     ("Turkon satış istihbaratı · haftalık", 10, False, LIGHT3)], next(z))]
radar += slicers(36)
radar += [
    text_card(40, 146, 900, 30, "Hafta Etiketi", 10.5, ACC, next(z), bold=True),
    text_card(40, 176, 1300, 110, "Başlık", 32, LIGHT, next(z), bold=True),
    text_card(40, 288, 1500, 28, "Özet Notu", 13, LIGHT2, next(z)),
]
KPI = [("Takip edilen rakip", "Rakip Sayısı", "K1 Alt"), ("Güncel fiyat oranı", "Güncel Oran", "K2 Alt"),
       ("Rakip yük arıyor", "Yük Arıyor", "K3 Alt"), ("Yetersiz ekipman", "Ekipman", "K4 Alt"),
       ("Direkt servis avantajı (gün)", "TT Farkı", "K5 Alt")]
for i, (label, value, foot) in enumerate(KPI):
    p = PANEL[f"kpi-{i + 1}"]
    radar += [textbox(p["x"] + 20, p["y"] + 14, p["w"] - 130, 26, [(label, 10, False, LIGHT2)], next(z)),
              text_card(p["x"] + 22, p["y"] + 46, p["w"] - 44, 52, value, 30, LIGHT, next(z), bold=True),
              text_card(p["x"] + 22, p["y"] + 100, p["w"] - 44, 28, foot, 9.5, LIGHT3, next(z))]


def panel_head(pid, title, sub=None):
    p = PANEL[pid]
    paras = [(title, 13, True, LIGHT)] + ([(sub, 9.5, False, LIGHT3)] if sub else [])
    return textbox(p["x"] + 20, p["y"] + 14, p["w"] - 40, 52 if sub else 32, paras, next(z))


p = PANEL["koridor"]
radar += [panel_head("koridor", "Pazar fiyat koridoru · 40' (USD)",
                     "En çok fiyat girilen 8 rota · rakip fiyatlarının en düşük – medyan – en yüksek değeri"),
          dark_table(p["x"] + 16, p["y"] + 68, p["w"] - 32, p["h"] - 80, [
              proj(col("RakipNavlun", "Servis"), "Servis"), proj(col("RakipNavlun", "POD"), "POD"),
              proj(mea("K Gözlem"), "Gözlem"), proj(mea("K Aralık"), "Rakip fiyat aralığı"),
              proj(mea("K Medyan"), "Medyan"), proj(mea("K En Ucuz"), "En ucuz rakip")], next(z),
              sort=[(mea("K Gözlem"), "Descending")], widths=[90, 110, 70, 480, 110, 210], image=(460, 18))]
p = PANEL["artislar"]
radar += [panel_head("artislar", "Genel fiyat artışları"),
          text_card(p["x"] + 22, p["y"] + 44, p["w"] - 44, 22, "Artış Alt", 9.5, LIGHT3, next(z)),
          dark_table(p["x"] + 16, p["y"] + 68, p["w"] - 32, p["h"] - 82, [
              proj(col("FiyatArtislari", "GecerliTarih"), "Tarih"), proj(col("FiyatArtislari", "Rakip"), "Rakip"),
              proj(col("FiyatArtislari", "ArtisAdi"), "Artış"), proj(col("FiyatArtislari", "LimanUlke"), "Liman"),
              proj(mea("Artış 20"), "20'"), proj(mea("Artış 40"), "40'"), proj(col("FiyatArtislari", "Durum"), "Durum")],
              next(z), sort=[(col("FiyatArtislari", "GecerliTarih"), "Descending")],
              widths=[100, 110, 90, 120, 70, 70, 100], font=10.5)]
p = PANEL["usec"]
radar += [panel_head("usec", "USEC · rakip 40' fiyatları", "USA-W rotası, rakip başına medyan, USD · turuncu = en ucuz"),
          visual(p["x"] + 12, p["y"] + 66, p["w"] - 24, p["h"] - 76, "clusteredBarChart", {
              "Category": {"projections": [proj(col("RakipNavlun", "Rakip"), "Rakip")]},
              "Y": {"projections": [proj(mea("USEC Medyan 40"), "Medyan 40'")]}},
              objects={**dark_axes(), "dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": mea("USEC Renk")}}}},
                                                     "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]},
              z=next(z), sort=[(mea("USEC Medyan 40"), "Ascending")])]
p = PANEL["sinyal"]
radar += [panel_head("sinyal", "Servis bazında pazar sinyali"),
          visual(p["x"] + 12, p["y"] + 46, p["w"] - 24, p["h"] - 56, "clusteredBarChart", {
              "Category": {"projections": [proj(col("Servisler", "Servis"), "Servis")]},
              "Y": {"projections": [proj(mea("Yük Arıyor %"), "Rakip yük arıyor"),
                                    proj(mea("Ekipman %"), "Yetersiz ekipman")]}},
              objects={**dark_axes(),
                       "legend": props(show=True, position="Top", fontSize=9, labelColor=solid(LIGHT2), showTitle=False),
                       "dataPoint": [{"properties": {"fill": solid(c)}, "selector": {"metadata": f"_Olculer.{m}"}}
                                     for m, c in [("Yük Arıyor %", ACC), ("Ekipman %", ACC2)]]},
              z=next(z))]
p = PANEL["notlar"]
radar += [panel_head("notlar", "Sahadan notlar & sefer aksaklıkları"),
          dark_table(p["x"] + 16, p["y"] + 50, p["w"] - 32, p["h"] - 62, [
              proj(col("SahaNotlari", "Tarih"), "Tarih"), proj(col("SahaNotlari", "Tur"), "Tür"),
              proj(col("SahaNotlari", "Rakip"), "Rakip"), proj(col("SahaNotlari", "Aciklama"), "Detay"),
              proj(col("SahaNotlari", "Etiket"), "Etiket")],
              next(z), sort=[(col("SahaNotlari", "Tarih"), "Descending")], widths=[90, 60, 100, 300, 110], font=10.5)]
radar += [textbox(40, 1044, 1400, 24, [("Kaynak: Rakip ve Pazar Verileri (SharePoint, haftalık dosyalar) · Fiyatlar "
                                        "KurTablosu ile USD'ye çevrilir · \"2150 - 2350\" gibi aralıklar orta noktayla alınır",
                                        8.5, False, LIGHT3)], next(z)),
          text_card(1500, 1046, 380, 22, "Altbilgi Sağ", 8.5, LIGHT3, next(z))]

detay = [textbox(40, 28, 900, 40, [("Rakip fiyat kayıtları · detay", 16, True, LIGHT)], next(z))] + slicers(26)
detay.append(dark_table(40, 90, 1840, 950, [proj(col("RakipNavlun", c), d) for c, d in [
    ("KayitNo", "#"), ("Hafta", "Hafta"), ("Servis", "Servis"), ("Rakip", "Rakip"), ("POL", "POL"), ("POD", "POD"),
    ("PB", "PB"), ("Ham20", "20' (giriş)"), ("Ham40", "40' (giriş)"), ("Fiyat40USD", "40' USD"),
    ("Aktarma", "Direkt/Aktarmalı"), ("AktarmaLimani", "Aktarma limanı"), ("HamTT", "TT"),
    ("YetersizEkipman", "Ekipman"), ("YukDurumu", "Yük durumu"), ("FiyatlamaTuru", "Fiyatlama"), ("Bolge", "Bölge"),
    ("Notlar", "Notlar")]], next(z), sort=[(col("RakipNavlun", "KayitNo"), "Ascending")]))


def page(name, display, visuals, image=None):
    base = REPORT / "definition" / "pages" / name
    bg = props(color=solid("#0B0A09"), transparency=0)
    if image:
        bg[0]["properties"]["image"] = {"image": {
            "name": lit(image), "scaling": lit("Fit"),
            "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1, "ItemName": image}}}}}
    write(base / "page.json", {
        "$schema": f"{SCHEMA}/item/report/definition/page/2.0.0/schema.json", "name": name, "displayName": display,
        "displayOption": "FitToPage", "height": 1080, "width": 1920,
        "objects": {"background": bg, "outspace": props(color=solid("#0B0A09"), transparency=0)}})
    for v in visuals:
        write(base / "visuals" / v["name"] / "visual.json", v)


THEME = {
    "name": "Rakip Radar Koyu",
    "dataColors": [ACC, ACC2, "#8C8782", "#5E8FD6", "#7BD88F", "#B48CE0", "#E87BA4", "#C8C6C4"],
    "background": PANEL_BG, "foreground": LIGHT, "tableAccent": ACC,
    "textClasses": {k: {"fontFace": "Segoe UI", "color": LIGHT} for k in ("callout", "title", "header", "label")},
    "visualStyles": {"*": {"*": {
        "background": [{"show": False}], "border": [{"show": False}], "dropShadow": [{"show": False}],
        "title": [{"show": False}], "visualHeader": [{"show": False}]}}},
}

if OUT.exists():
    for d in (REPORT, MODEL, OUT / f"{NAME}.pbip"):
        shutil.rmtree(d, ignore_errors=True) if d.is_dir() else d.unlink(missing_ok=True)
page("radar", "Radar", radar, image=BG)
page("detay", "Detay", detay)
write(OUT / f"{NAME}.pbip", {"$schema": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
                             "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}})
for folder, kind in [(REPORT, "Report"), (MODEL, "SemanticModel")]:
    write(folder / ".platform", {"$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
                                 "metadata": {"type": kind, "displayName": NAME}, "config": {"version": "2.0", "logicalId": uid()}})
write(MODEL / "definition.pbism", {"$schema": f"{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json",
                                   "version": "4.0", "settings": {}})
write(MODEL / "model.bim", model)
write(REPORT / "definition.pbir", {"$schema": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json", "version": "4.0",
                                   "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
write(REPORT / "definition" / "version.json", {"$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json",
                                               "version": "2.0.0"})
write(REPORT / "definition" / "report.json", {
    "$schema": f"{SCHEMA}/item/report/definition/report/2.0.0/schema.json",
    "themeCollection": {"customTheme": {"name": "Radar_Tema.json", "reportVersionAtImport": "5.59", "type": "RegisteredResources"}},
    "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources", "items": [
        {"name": "Radar_Tema.json", "path": "Radar_Tema.json", "type": "CustomTheme"},
        {"name": BG, "path": BG, "type": "Image"}]}],
    "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                 "defaultDrillFilterOtherVisuals": True, "useEnhancedTooltips": True}})
write(REPORT / "definition" / "pages" / "pages.json", {
    "$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": ["radar", "detay"], "activePageName": "radar"})
write(REPORT / "StaticResources" / "RegisteredResources" / "Radar_Tema.json", THEME)
shutil.copyfile(HERE / "katmanlar" / "pbi-arkaplan.png", REPORT / "StaticResources" / "RegisteredResources" / BG)
write(OUT / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf")
print(f"{len(measures)} ölçü, {len(radar)} + {len(detay)} görsel → {OUT}")
