# Veri Kaynakları ve İndirme Rehberi

## 🎯 Ana Kaynaklar

### 1. MEB Resmi Kaynakları (Öncelikli)

#### MEB Örnek Sorular
- **URL:** https://odsgm.meb.gov.tr/www/ornek-sorular/icerik/listesi
- **İçerik:** Her ay yayınlanan örnek sorular
- **Format:** PDF
- **Yıllar:** 2018-2024

#### MEB Çıkmış Sorular
- **URL:** https://www.meb.gov.tr/meb_iys_dosyalar/2018_06/29112223_2018_LGS_Soru_Kitapciklari_ve_Cevap_Anahtarlari.zip
- **İçerik:** Geçmiş yıllara ait LGS soru kitapçıkları
- **Format:** PDF/ZIP
- **Yıllar:** 2018-2024

### 2. Eğitim Portalları (Açık Erişim)

#### DersMatematik.net
- **URL:** https://dersmatematik.net/lgs/
- **İçerik:** 2018-2025 LGS çıkmış sorular
- **Format:** PDF
- **Avantaj:** Tüm yıllar tek sayfada

#### Bilgenç.com
- **URL:** https://www.bilgenc.com/lgs-matematik-cikmis-sorular/
- **İçerik:** 2018'den itibaren LGS Matematik soruları
- **Format:** PDF

#### Unikoçu.com
- **URL:** https://unikocu.com/lgs-matematik-cikmis-sorular-ve-cevaplari-pdf/
- **İçerik:** 2018-2023 LGS Matematik soruları
- **Format:** PDF

#### Matematikciler.com
- **URL:** https://www.matematikciler.com/lgs-sorulari-ve-cevaplari/
- **İçerik:** 2018'den itibaren soru kitapçıkları
- **Format:** PDF

#### Fimatematik.com
- **URL:** https://www.fimatematik.com/2024/10/lgs-cikmis-sorular-ve-cevaplari-2018-2023.html
- **İçerik:** 2018-2024 LGS soruları
- **Format:** PDF

### 3. YouTube Kaynakları (Görsel İçerik)

- **Pulat Akademi:** LGS çıkmış sorular çözümleri
- **Matematik Öğretmenleri:** Soru çözüm videoları
- **Not:** Videolardan ekran görüntüsü alınabilir

---

## 📥 Otomatik İndirme

Aşağıdaki script ile otomatik indirme yapabilirsiniz:

```bash
python src/data/download_data.py --source meb --year 2023
python src/data/download_data.py --source dersmatematik --all
```

---

## 🔍 Kareköklü İfadeler Filtreleme

İndirilen PDF'lerden sadece kareköklü ifadeler sorularını çıkarmak için:

```bash
python src/data/ingest.py --config configs/data_ingest.yaml
```

Bu script otomatik olarak:
- PDF'lerden metin çıkarır
- "kök", "√", "kareköklü" gibi anahtar kelimeleri arar
- İlgili soruları filtreler

---

## 📋 Manuel İndirme Adımları

### Adım 1: MEB Örnek Sorular
1. https://odsgm.meb.gov.tr/www/ornek-sorular/icerik/listesi adresine git
2. Matematik örnek sorularını seç
3. PDF'leri indir
4. `data/raw/lgs_meb_koklu/` klasörüne koy

### Adım 2: Çıkmış Sorular
1. Yukarıdaki eğitim portallarından birini seç
2. Matematik sorularını indir
3. `data/raw/lgs_meb_koklu/` klasörüne koy

### Adım 3: Dosya Adlandırma
Dosyaları şu formatta adlandır:
- `LGS_2023_Matematik.pdf`
- `LGS_2024_Matematik.pdf`
- `MEB_Ornek_Sorular_2024_Aralik.pdf`

---

## ⚠️ Önemli Notlar

1. **Telif Hakları:** Sadece kamuya açık MEB kaynaklarını kullan
2. **Veri Kalitesi:** PDF'lerin OCR gerektirebileceğini unutma
3. **Minimum Veri:** En az 100 soru hedefliyoruz
4. **Filtreleme:** Sadece kareköklü ifadeler konusuna odaklan

---

## 🚀 Hızlı Başlangıç

1. Yukarıdaki kaynaklardan PDF'leri indir
2. `data/raw/lgs_meb_koklu/` klasörüne koy
3. `python src/data/ingest.py --config configs/data_ingest.yaml` çalıştır
4. Sonuçları kontrol et

