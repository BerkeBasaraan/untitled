// katmanlar/ klasöründen düzenlenebilir PowerPoint üretir (1920x1080 = 20" x 11.25").
// Slayt 1: her katman ayrı nesne (Seçim Bölmesi'nde adlarıyla); metinler düzenlenebilir metin kutusu,
// hap ve etiketler PowerPoint şekli. Slayt 2: tamamlanmış tasarım (referans).
// Kullanım: node dashboard/rakip/katman_pptx.js   (gerekirse: npm install pptxgenjs)
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const DIR = path.join(__dirname, "katmanlar");
const L = JSON.parse(fs.readFileSync(path.join(DIR, "katmanlar.json"), "utf8"));
const FONT = "Segoe UI";
const px = v => v / 96;          // piksel → inç
const pt = v => v * 0.75;        // CSS px → punto
const BG = [20, 18, 16];         // cam panellerin yaklaşık zemin rengi (yarı saydam metin renkleri için)

// "rgba(245, 242, 238, 0.68)" → koyu zemin üzerinde görünen düz renk
function hex(css) {
  const [r, g, b, a = 1] = css.match(/[\d.]+/g).map(Number);
  return [r, g, b].map((c, i) => Math.round(c * a + BG[i] * (1 - a)).toString(16).padStart(2, "0")).join("").toUpperCase();
}
const bold = w => Number(w) >= 600;

const pres = new pptxgen();
pres.defineLayout({ name: "FHD", width: 20, height: 11.25 });
pres.layout = "FHD";
pres.title = "Rakip ve Pazar Radarı - katmanlar";

const s = pres.addSlide();
s.background = { color: "0B0A09" };
const img = (file, x, y, w, h, name) =>
  s.addImage({ path: path.join(DIR, file), x: px(x), y: px(y), w: px(w), h: px(h), objectName: name });
const text = (t, b, name, extra = {}) =>
  s.addText(t, {
    x: px(b.x), y: px(b.y), w: px(b.w * 1.12 + 4), h: px(Math.max(b.h, 14)), margin: 0, valign: "top",
    fontFace: FONT, fontSize: pt(b.size), bold: bold(b.weight), color: hex(b.color), isTextBox: true, objectName: name,
    ...extra,
  });

// Arka plan katmanları
img("01-gemi-fotograf.png", 0, 0, 1920, 1080, "Arka plan - gemi fotoğrafı");
img("02-karartma.png", 0, 0, 1920, 1080, "Arka plan - karartma");
for (const p of L.panels) img(p.file, p.x, p.y, p.w, p.h, `Panel - ${p.id}`);
img("logo.png", L.logo.x, L.logo.y, L.logo.w, L.logo.h, "Logo");

// Üst bölüm metinleri
L.brand.forEach((b, i) => text(b.text, b, i ? "Metin - alt başlık" : "Metin - panel adı"));
text(L.week.text.toLocaleUpperCase("tr-TR"), L.week, "Metin - hafta etiketi", { charSpacing: 1.5 });
const hl = L.headline;
const [first, second] = hl.html.split("<br>");
const [before, rest] = first.split("<em>");
const [accent, after] = rest.split("</em>");
const unescape = t => t.replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#39;/g, "'");
text([
  { text: unescape(before) },
  { text: unescape(accent), options: { color: "FF7A2F" } },
  { text: unescape(after), options: { breakLine: true } },
  { text: unescape(second) },
], { ...hl, w: hl.w }, "Metin - ana başlık", { lineSpacingMultiple: 0.95, h: px(hl.h + 10) });
text(L.subline.text, L.subline, "Metin - özet notu");

// Filtre hapları (PowerPoint şekli + metin)
for (const p of L.pills) {
  s.addText(p.text.replace("⌄", "▾"), {
    shape: pres.ShapeType.roundRect, rectRadius: px(p.h / 2),
    x: px(p.x), y: px(p.y), w: px(p.w), h: px(p.h), margin: 0, align: "center", valign: "middle",
    fontFace: FONT, fontSize: 10.5, bold: p.on, color: p.on ? "1A0F08" : "B3AFAB",
    fill: { color: p.on ? "FF7A2F" : "141210", transparency: p.on ? 0 : 45 },
    line: { color: p.on ? "FF7A2F" : "FFFFFF", transparency: p.on ? 0 : 88, width: 0.75 },
    objectName: `Filtre - ${p.text}`,
  });
}

// Panel başlıkları, alt başlıklar, KPI etiketleri, lejantlar
const TAG = { warn: ["F6B73C", 82], hot: ["FF7A2F", 80], ok: ["7BD88F", 84], mute: ["FFFFFF", 92] };
for (const p of L.panels) {
  if (p.title) text(p.title.text, p.title, `Metin - ${p.id} başlık`, p.kpi ? { w: px(p.title.w - (p.tag ? p.tag.w + 8 : 0)) } : {});
  if (p.sub) text(p.sub.text, p.sub, `Metin - ${p.id} açıklama`, { w: px(p.w - 48) });
  if (p.tag) {
    const [c, tr] = TAG[p.tag.cls] || TAG.mute;
    s.addText(p.tag.text, {
      shape: pres.ShapeType.roundRect, rectRadius: px(10),
      x: px(p.tag.x - 4), y: px(p.tag.y), w: px(p.tag.w + 8), h: px(p.tag.h), margin: 0, align: "center", valign: "middle",
      fontFace: FONT, fontSize: 8.25, bold: true, color: p.tag.cls === "mute" ? "C9C6C2" : c,
      fill: { color: c, transparency: tr }, line: { type: "none" }, objectName: `Etiket - ${p.id}`,
    });
  }
  for (const g of p.legend) {
    s.addShape(pres.ShapeType.roundRect, {
      x: px(g.x), y: px(g.y + 3), w: px(10), h: px(10), rectRadius: px(3),
      fill: { color: hex(g.color) }, line: { type: "none" }, objectName: `Lejant işareti - ${g.text}`,
    });
    text(g.text, { x: g.x + 16, y: g.y, w: g.w - 16, h: g.h, size: 12, weight: "400", color: "rgba(245,242,238,.68)" },
      `Lejant - ${g.text}`);
  }
}
L.footer.forEach((f, i) => text(f.text, f, i ? "Metin - altbilgi sağ" : "Metin - altbilgi sol",
  i ? { align: "right", x: px(f.x - f.w * 0.12 - 4) } : {}));

// Slayt 2: referans
const r = pres.addSlide();
r.addImage({ path: path.join(__dirname, "rakip-panel.png"), x: 0, y: 0, w: 20, h: 11.25, objectName: "Referans - tamamlanmış tasarım" });

pres.writeFile({ fileName: path.join(__dirname, "Rakip-Pazar-Radari-katmanlar.pptx") }).then(f => console.log(f));
