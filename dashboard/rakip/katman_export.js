// rakip-panel.html'i parçalara ayırır: gemi fotoğrafı, karartma katmanı, her cam panel (şeffaf köşeli PNG), logo
// ve düzenlenebilir metinlerin konum/stil bilgisi (katmanlar.json). PowerPoint dosyası katman_pptx.js ile üretilir.
// Kullanım: node dashboard/rakip/katman_export.js
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const DIR = __dirname;
const OUT = path.join(DIR, "katmanlar");
const PAGE = "file://" + path.join(DIR, "rakip-panel.html");

(async () => {
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(PAGE);
  await page.waitForTimeout(800);

  // 1) Metin ve şekil konumları (veri içeriği hariç)
  const layout = await page.evaluate(() => {
    const box = e => { const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; };
    const style = e => { const s = getComputedStyle(e); return { size: parseFloat(s.fontSize), weight: s.fontWeight, color: s.color, spacing: s.letterSpacing }; };
    const panels = [...document.querySelectorAll(".glass")].map((g, i) => {
      const kpi = g.classList.contains("kpi");
      const title = kpi ? g.querySelector(".label") : g.querySelector("h2");
      const tag = kpi ? g.querySelector(".tag") : null;
      const sub = g.querySelector(".sub");
      const legend = [...g.querySelectorAll(".legend span")].map(s => ({ ...box(s), text: s.textContent.trim(), color: getComputedStyle(s.querySelector("i")).backgroundColor }));
      return {
        id: kpi ? `kpi-${i + 1}` : ["koridor", "artislar", "usec", "sinyal", "notlar"][i - 5],
        ...box(g), kpi,
        title: title && { ...box(title), text: kpi ? title.firstChild.textContent.trim() : title.textContent.trim(), ...style(title) },
        tag: tag && { ...box(tag), text: tag.textContent.trim(), cls: tag.className.replace("tag", "").trim() },
        sub: sub && { ...box(sub), text: sub.textContent.trim(), ...style(sub) },
        legend,
      };
    });
    const h1 = document.querySelector(".hero h1");
    return {
      panels,
      pills: [...document.querySelectorAll(".pill")].map(p => ({ ...box(p), text: p.textContent.trim(), on: p.classList.contains("on") })),
      logo: box(document.querySelector(".logo")),
      brand: [...document.querySelectorAll(".brand b, .brand span")].map(e => ({ ...box(e), text: e.textContent.trim(), ...style(e) })),
      week: { ...box(document.querySelector(".hero .week")), text: document.querySelector(".hero .week").textContent.trim(), ...style(document.querySelector(".hero .week")) },
      headline: { ...box(h1), html: h1.innerHTML, ...style(h1) },
      subline: { ...box(document.querySelector(".hero p")), text: document.querySelector(".hero p").textContent.trim(), ...style(document.querySelector(".hero p")) },
      footer: [...document.querySelectorAll(".footer span")].map(e => ({ ...box(e), text: e.textContent.trim(), ...style(e) })),
    };
  });
  fs.writeFileSync(path.join(OUT, "katmanlar.json"), JSON.stringify(layout, null, 1));

  // 2) Logo (şeffaf)
  await (await page.$(".logo")).screenshot({ path: path.join(OUT, "logo.png"), omitBackground: true });

  // 3) Karartma katmanı: yalnızca gradyan, arka plan şeffaf
  await page.addStyleTag({ content: "body > *:not(.shade){visibility:hidden!important} body{background:transparent!important}" });
  await page.screenshot({ path: path.join(OUT, "02-karartma.png"), omitBackground: true });

  // 4) Boş cam paneller: fotoğraf + karartma + paneller, içerik gizli → tam ekran görüntüsünden kırpılır
  await page.goto(PAGE);
  await page.waitForTimeout(800);
  await page.addStyleTag({ content: ".glass > *, .hero, .brand, .filters, .footer {visibility:hidden!important}" });
  await page.screenshot({ path: path.join(OUT, "_paneller-tam.png") });

  // 5) Power BI sayfa arka planı: fotoğraf + karartma + boş paneller + logo + KPI etiketleri (metinler Power BI'da)
  await page.goto(PAGE);
  await page.waitForTimeout(800);
  await page.addStyleTag({ content: ".glass > *:not(.label), .hero, .brand > div:last-child, .filters, .footer {visibility:hidden!important} .kpi .label {color:transparent!important}" });
  await page.screenshot({ path: path.join(OUT, "pbi-arkaplan.png") });

  fs.copyFileSync(path.join(DIR, "..", "mockup", "teu-gemi-arkaplan.png"), path.join(OUT, "01-gemi-fotograf.png"));
  await browser.close();
})();
