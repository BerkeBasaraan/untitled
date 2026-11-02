# Rakip & Pazar Radarı – Power BI projesi

## Açmak ve .pbix olarak kaydetmek

1. ZIP'i bir klasöre çıkarın ve `Rakip-Pazar-Radari.pbip` dosyasını Power BI Desktop ile açın.
2. **Yenile**'ye basın. İlk açılışta `KaynakModu = Ornek` olduğundan modele gömülü örnek Excel (Hafta 45) kullanılır.
3. **Dosya → Farklı kaydet → .pbix**.

> Örnek Excel dosyası modelin içine gömülüdür. Bu dosyayı herkese açık bir yere (örneğin herkese açık GitHub deposu) koymayın.

## SharePoint klasörüne bağlamak

**Giriş → Verileri dönüştür → Parametreleri düzenle**:

| Parametre | Değer |
|---|---|
| `KaynakModu` | `SharePoint` |
| `SharePointSite` | Site adresi, örneğin `https://sirketiniz.sharepoint.com/sites/Satis` (klasörün değil, sitenin adresi) |
| `SharePointKlasor` | Klasör yolunda geçen ad, örneğin `Rakip ve Pazar` |

Klasördeki dosyalar **W44.xlsx** biçiminde adlandırılmalı: adındaki sayı dosya haftası olur. Yıl, dosyanın değiştirilme tarihinden alınır.

### Neden "dosya haftası"?

Her haftalık dosya pazarın tam fotoğrafıdır: satırlar her hafta yerinde güncellenir. Dosyalar alt alta eklenince aynı satır her dosyada tekrar eder. Bu yüzden her satıra dosya haftası eklenir; sağ üstteki **Hafta** dilimleyicisi hangi haftanın fotoğrafına bakıldığını seçer. Seçim yoksa ölçüler en son dosyayı kullanır.

## Power Query'de neler var?

| Sorgu | Açıklama |
|---|---|
| `DosyaListesi` | Örnek dosya veya SharePoint klasöründeki .xlsx dosyaları + DosyaHaftasi / DosyaSira |
| `fnSayfa` | Sayfadaki başlık satırını bulup tabloyu ondan başlatır (üstteki boş satırlar ve notlar atlanır) |
| `fnTemizMetin` | Baştaki/sondaki boşlukları ve çift boşlukları temizler; boş metni boş değer yapar |
| `fnSayi` | "2150 - 2350" → 2250 (orta nokta), "Kapalı", "-", "yok" → boş; Excel'in tarihe çevirdiği "8-9" → 8,5 |
| `RakipEsleme` | Aynı rakibin farklı yazımları (CULINES → CUL LINES). Yeni yazım farkı çıkarsa satır ekleyin |
| `KurTablosu` | **USD dönüşümü burada:** PB başına 1 birimin USD karşılığı. Şimdilik hepsi 1 |
| `RakipNavlun`, `GemiTakibi`, `FiyatArtislari`, `PiyasaBilgisi` | Dört sayfa, tüm dosyalardan birleşik ve temizlenmiş |
| `SahaNotlari` | Piyasa notları + gemi takibindeki sefer aksaklıkları tek akışta |
| `Dosyalar`, `Servisler` | Hafta ve servis dilimleyicileri için |

## Sayfalar

- **Radar:** tasarımdaki panel. Arka plan resmi (`Radar_Arkaplan.png`) gemi fotoğrafı, karartma, boş cam paneller, logo ve KPI etiketlerinden oluşur; başlıklar düzenlenebilir metin kutusu, sayılar ve grafikler Power BI görselidir. Ana başlık ve özet notu ölçülerden gelir (`Başlık`, `Özet Notu`), her hafta kendiliğinden güncellenir.
- **Detay:** tüm rakip fiyat kayıtları (girilen ham değer ve USD karşılığı yan yana).

## Ölçüler hakkında

- "Pazar yumuşak / dengeli / sıkı" eşikleri `Başlık` ölçüsünde: "yük arıyor" oranı %20 ve üstü yumuşak, %10–20 dengeli.
- Fiyat koridoru en çok fiyat girilen 10 rotayı gösterir (en az 3 gözlem); `Koridorda` ölçüsünden değiştirilebilir.
- USEC grafiği `USEC Medyan 40` ölçüsündeki POD filtresiyle çalışır; başka bir rota için ölçüyü kopyalayıp POD'u değiştirin.
