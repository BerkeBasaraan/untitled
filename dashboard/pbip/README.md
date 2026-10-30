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

Sayfa üç katmandan oluşur:

1. **Sayfa arka planı:** gemi fotoğrafı. Dosyada koyu düz renk olarak gelir, fotoğrafı siz eklersiniz (aşağıda).
2. **Panel katmanı:** sayfanın tamamını kaplayan bir Görüntü görseli (`TEU_Panel_Katmani.png`). Yarı saydam koyu paneller, ikonlar ve sabit başlıklar bu şeffaf PNG'de.
3. **Veri görselleri:** sayılar, grafikler, gösterge ve dilimleyiciler. Arka planları şeffaf.

**Gemi fotoğrafını eklemek:**
1. Panel sayfasında tuvalin boş bir yerine tıklayın (hiçbir görsel seçili olmasın).
2. **Biçim → Kanvas arka planı → Resim → Gözat** ile fotoğrafı seçin.
3. **Görüntü sığdırma: Doldur**, **Saydamlık: %0** yapın.

En iyi sonucu 1920×1080 veya daha büyük, yatay, üst-orta kısmı sakin bir fotoğraf verir. Paneller fotoğrafın alt yarısını kapatır.

- Power BI görsellerin arkasını bulanıklaştıramaz. Bu yüzden paneller buzlu cam değil, yarı saydam koyudur.
- Bir başlığı veya ikonu değiştirmek için `dashboard/mockup/teu-glass.html?bg&layer` sayfasını düzenleyip şeffaf arka planlı 1920×1080 ekran görüntüsünü yeniden alın, sonra betiği çalıştırın.
- Panel katmanını yanlışlıkla seçip taşımamak için Seçim bölmesinde (Görünüm → Seçim) gizleyip açabilir veya en alta sabit tutabilirsiniz.
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
