# 🚀 Hızlı Başlangıç - Veri Toplama

## Yöntem 1: Otomatik İndirme (Önerilen)

### Adım 1: Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### Adım 2: Otomatik İndirme Scriptini Çalıştır

#### MEB Örnek Sorular (Tüm Yıllar)
```bash
python src/data/download_data.py --source meb --all
```

#### Belirli Bir Yıl
```bash
python src/data/download_data.py --source meb --year 2023
```

#### DersMatematik.net'ten İndir
```bash
python src/data/download_data.py --source dersmatematik --all
```

### Adım 3: İndirilen Dosyaları Kontrol Et
```bash
ls -lh data/raw/lgs_meb_koklu/
```

---

## Yöntem 2: Manuel İndirme (Daha Güvenilir)

### Seçenek A: MEB Resmi Sitesi

1. **MEB Örnek Sorular:**
   - Git: https://odsgm.meb.gov.tr/www/ornek-sorular/icerik/listesi
   - "Matematik" kategorisini seç
   - PDF'leri indir
   - `data/raw/lgs_meb_koklu/` klasörüne koy

2. **MEB Çıkmış Sorular:**
   - Git: https://www.meb.gov.tr/meb_iys_dosyalar/2018_06/29112223_2018_LGS_Soru_Kitapciklari_ve_Cevap_Anahtarlari.zip
   - ZIP'i indir ve aç
   - Matematik PDF'lerini `data/raw/lgs_meb_koklu/` klasörüne koy

### Seçenek B: Eğitim Portalları

#### DersMatematik.net (En Kolay)
1. Git: https://dersmatematik.net/lgs/
2. "Matematik" başlığına tıkla
3. PDF linklerine tıkla ve indir
4. `data/raw/lgs_meb_koklu/` klasörüne koy

#### Bilgenç.com
1. Git: https://www.bilgenc.com/lgs-matematik-cikmis-sorular/
2. İstediğin yılın PDF'ini indir
3. `data/raw/lgs_meb_koklu/` klasörüne koy

### Dosya Adlandırma
Dosyaları şu formatta adlandır:
- `LGS_2023_Matematik.pdf`
- `LGS_2024_Matematik.pdf`
- `MEB_Ornek_Sorular_2024_Aralik.pdf`

---

## Yöntem 3: Görsel Dosyaları Toplama

### YouTube'dan Ekran Görüntüsü
1. LGS matematik soru çözüm videolarını aç
2. Kareköklü ifadeler sorularını bul
3. Ekran görüntüsü al (Cmd+Shift+4 / Windows+Shift+S)
4. `data/raw/lgs_meb_koklu/images/` klasörüne kaydet
5. Dosya adı: `soru_001.jpg`, `soru_002.png` gibi

### PDF'lerden Görsel Çıkarma
PDF'lerden görsel çıkarmak için script hazırlanacak (ileride).

---

## ✅ Sonraki Adımlar

Verileri topladıktan sonra:

1. **Veri Çıkarma:**
   ```bash
   python src/data/ingest.py --config configs/data_ingest.yaml
   ```

2. **Sonuçları Kontrol Et:**
   ```bash
   cat data/interim/extracted_questions.json | head -20
   ```

3. **Veri Temizleme:**
   ```bash
   python src/data/preprocess.py \
     --input data/interim/extracted_questions.json \
     --output data/processed/cleaned_questions.csv
   ```

---

## 📊 Minimum Veri Gereksinimleri

- **Hedef:** En az 100 soru
- **Önerilen:** 200+ soru (daha iyi model performansı için)
- **Yıllar:** 2018-2024 arası (mümkünse tümü)

---

## 🆘 Sorun Giderme

### İndirme Scripti Çalışmıyor
- İnternet bağlantını kontrol et
- Bazı siteler bot trafiğini engelleyebilir (manuel indirme yap)
- `requests` ve `beautifulsoup4` yüklü mü kontrol et

### PDF'ler Açılmıyor
- PDF'ler şifreli olabilir (manuel olarak açıp kaydet)
- PDF'ler bozuk olabilir (yeniden indir)

### Yeterli Soru Bulunamıyor
- Farklı kaynakları dene
- Görsel dosyaları da ekle (OCR ile işlenecek)
- Manuel olarak soru ekleyebilirsin (JSON formatında)

---

## 💡 İpuçları

1. **Öncelik:** MEB resmi kaynaklarını kullan (en güvenilir)
2. **Çeşitlilik:** Farklı yıllardan soru topla
3. **Kalite:** PDF kalitesi yüksek olsun (OCR için önemli)
4. **Organizasyon:** Dosyaları düzenli adlandır

