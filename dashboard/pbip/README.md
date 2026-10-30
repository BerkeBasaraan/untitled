# TEU Challenge – Power BI projesi (demo verisi)

Bu klasör, tasarım maketinin (`dashboard/mockup`) Power BI'da kurulmuş halidir. Dosya biçimi **Power BI Project (.pbip)**: rapor ve veri modeli düz metin dosyaları olarak saklanır.

## Açmak ve .pbix olarak kaydetmek

1. Power BI Desktop'ın güncel bir sürümü gerekir (2025 ve sonrası).
2. `TEU-Challenge.pbip` dosyasını Power BI Desktop ile açın.
3. Veri model içinde gömülü olduğu için **Yenile**'ye basın (internet veya kaynak bağlantısı gerekmez).
4. **Dosya → Farklı kaydet → .pbix** ile tek dosya olarak kaydedin.

Daha eski bir Desktop sürümünde açılmazsa: **Dosya → Seçenekler → Önizleme özellikleri** altında
"Power BI Project (.pbip) save option" ve "Store reports using enhanced metadata format (PBIR)" seçeneklerini açıp Desktop'ı yeniden başlatın.

## İçerik

| Sayfa | Görseller |
|---|---|
| Panel | Konteyner gemisi arka planlı koyu tasarım: selamlama, 3 KPI kartı (konteyner tipine göre TEU, son 7 gün sen vs bir öndeki, bu haftanın günlük TEU'su), hedefe kalan, şirket yarışı, kişisel hedef göstergesi |
| Liderlik | 4 KPI kartı, ilk 15 + sen liderlik grafiği (250 TEU hedef çizgisiyle), yarış çizgi grafiği (sen / lider / bir öndeki / bir arkadaki), son girişler, bölge sıralaması |
| Bölgeler | Bölge KPI'ları, bölge toplamları, bölgelerin kümülatif yarışı, bölge özeti tablosu |
| Detay | Tüm girişler tablosu |

Tablolar: `Kisiler` (42 kişi, 5 bölge), `Challenge` (393 sahte giriş, 1–27 Ekim 2026), `Tarih`, `Seri` (yarış grafiği lejantı), `_Olculer` (tüm DAX ölçüleri, açıklamalarıyla).

## Panel sayfası nasıl kuruldu?

Power BI görsellerin arkasını bulanıklaştıramaz. Bu yüzden gemi fotoğrafı, buzlu cam paneller, ikonlar ve sabit başlıklar tek bir **sayfa arka plan resmine** (`TEU_Panel_Arkaplan.png`) gömüldü. Veriye bağlı her şey (sayılar, grafikler, gösterge, dilimleyiciler) bu resmin üstünde arka planı şeffaf Power BI görselleridir.

**Fotoğrafı değiştirmek için:**
1. Fotoğraf küçükse (1000 px'ten dar) önce `dashboard/mockup/upscale_photo.py` ile yapay zekâyla 4 kat büyütün.
2. `python3 dashboard/mockup/grade_photo.py <fotoğraf>`: fotoğrafı keskin kalacağı boyutta üst-ortaya yerleştirir, kenarlarını aynı fotoğrafın bulanık koyu kopyasına karıştırır ve tasarımın ışığına göre renklendirir (`teu-gemi-arkaplan.png`). Geminin konumu ve boyutu betiğin başındaki ayarlarla değişir.
3. `dashboard/mockup/teu-glass.html?photo=teu-gemi-arkaplan.png&bg` sayfasının 1920×1080 ekran görüntüsünü `teu-panel-arkaplan.png` olarak alın.
4. `python3 dashboard/pbip/build_pbip.py` ile projeyi yeniden üretin.

Bunun yerine hazır bir resmi Power BI'da da koyabilirsiniz: Panel sayfasında boş bir yere tıklayın, **Biçim → Kanvas arka planı → Resim** ile seçin, **Görüntü sığdırma: Sığdır** yapın. Paneller resmin içinde olduğu için yalnızca fotoğraf koyarsanız kartlar okunaksız kalır. Bu durumda `dashboard/mockup/teu-panel-katmani.png` (şeffaf panel katmanı) dosyasını bir Görüntü görseli olarak sayfanın en altına ekleyin.

- Görselleri taşırsanız arka plandaki cam panellerle hizası bozulur. Görünüm → Kılavuz çizgileri / Izgaraya yasla seçenekleri işe yarar.
- Sol menü ikonları, "TEU Ekle" ve "Rapor Oluştur" düğmeleri resmin parçasıdır, tıklanmaz. Sayfalar arasında Power BI'ın sayfa sekmeleriyle geçin.

## "Sen" kim?

Raporu açan kişi `USERPRINCIPALNAME()` ile bulunur ve `Kisiler[Email]` ile eşleştirilir. Desktop'ta e-postanız demo listesinde olmadığı için rapor **Can Demir**'i "sen" olarak gösterir. Gerçek veride herkes kendini turuncu görür.

## Doğru açıldığını kontrol etmek için beklenen değerler

| Kart | Beklenen |
|---|---|
| Senin TEU'n | 186 · Hedef 250 TEU · %74 · 64 TEU kaldı |
| Sıran | 3. · 42 kişi içinde · ▲ 1 sıra yükseldin (4. → 3.) |
| Bir üst sıraya kalan | 14 TEU · Önündeki: Mehmet Tunç · 200 TEU |
| Bugün (sen) | +16 TEU · Şirket geneli: +45 TEU · 9 giriş |
| Liderlik başlığı | Lider Ayşe Kaya (240 TEU) · Sen 3. sıradasın |
| Bölge başlığı | Marmara bölgesi önde · Marmara çubuğu 1.028 TEU |

## Gerçek veriye geçiş

1. **Veri dönüştür**'de `Kisiler` ve `Challenge` sorgularının `Kaynak` adımını kendi kaynağınızla değiştirin. Sütun adları aynı kalmalı: `KisiID, Kisi, Email, Bolge, Yonetici, HedefTEU` ve `KayitID, KisiID, YuklemeZamani, TEU`.
2. `Tarih` sorgusundaki başlangıç ve bitiş tarihlerini challenge dönemine göre güncelleyin.
3. `Son Veri Günü` ölçüsünü `TODAY ()` olarak değiştirin. Demo için bu ölçü "bugün" yerine verideki son günü kullanır.

## Yeniden üretmek

```
python3 dashboard/pbip/build_pbip.py
```
