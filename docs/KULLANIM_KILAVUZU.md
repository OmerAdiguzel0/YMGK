# Kullanım Kılavuzu

## Hızlı Başlangıç

### 1. Ortam Kurulumu

```bash
# Sanal ortam oluştur
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# veya
.venv\Scripts\activate  # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt
```

**Not:** OCR için Tesseract yüklü olmalı:
- macOS: `brew install tesseract tesseract-lang`
- Linux: `sudo apt-get install tesseract-ocr tesseract-ocr-tur`
- Windows: [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)

### 2. Veri Hazırlama

#### PDF Dosyaları
PDF dosyalarını şu klasöre koy:
```
data/raw/lgs_meb_koklu/
```

Dosya adlandırma örnekleri:
- `LGS_2023_Matematik.pdf`
- `LGS_2024_Matematik.pdf`
- `MEB_Ornek_Sorular_2024.pdf`
- `Deneme_2024_Matematik.pdf`

#### Görsel Dosyalar
Soru görsellerini şu klasöre koy:
```
data/raw/lgs_meb_koklu/images/
```

Dosya formatları: `.jpg`, `.png`, `.jpeg`

#### Manuel JSON/CSV Dosyaları
Eğer soruları zaten yapılandırılmış formatta hazırladıysan:
```
data/raw/lgs_meb_koklu/manual/
```

JSON formatı örneği:
```json
[
  {
    "question_id": "LGS_2023_MAT_15",
    "question_text": "√48 + √12 işleminin sonucu kaçtır?",
    "options": ["A) 6√3", "B) 8√3", "C) 10√3", "D) 12√3"],
    "correct_answer": "A",
    "solution_text": "√48 = 4√3, √12 = 2√3, toplam = 6√3",
    "difficulty": "orta",
    "question_type": "işlem",
    "year": 2023,
    "topic": "kareköklü_ifadeler"
  }
]
```

### 3. Veri Çıkarma (Extraction)

Verileri hazırladıktan sonra:

```bash
python src/data/ingest.py --config configs/data_ingest.yaml
```

Bu komut:
- PDF dosyalarından metin çıkarır
- Görsellerden OCR ile metin çıkarır
- JSON dosyalarını okur
- Tüm soruları `data/interim/extracted_questions.json` dosyasına kaydeder

### 4. Veri Temizleme

```bash
python src/data/preprocess.py \
  --input data/interim/extracted_questions.json \
  --output data/processed/cleaned_questions.csv
```

### 5. Model Eğitimi

```bash
python src/pipelines/train.py --config configs/train_baseline.yaml
```

### 6. Tahmin Yapma

```bash
python src/pipelines/predict.py --question "√16 + √9 işleminin sonucu kaçtır?"
```

---

## Sorun Giderme

### OCR Çalışmıyor
- Tesseract yüklü mü kontrol et: `tesseract --version`
- Türkçe dil paketi yüklü mü: `tesseract --list-langs` (içinde `tur` olmalı)

### PDF'den Metin Çıkmıyor
- PDF şifreli olabilir
- PDF görsel tabanlı olabilir (OCR gerekebilir)
- `pdfplumber` yerine `PyPDF2` deneyin

### Görsel İşleme Hataları
- Görsel formatını kontrol et (PNG, JPG desteklenir)
- Görsel çok küçük veya çok büyük olabilir
- Görsel kalitesi düşük olabilir (bulanık, düşük çözünürlük)

---

## Sonraki Adımlar

1. ✅ Verileri topla ve klasörlere koy
2. ✅ `ingest.py` scriptini çalıştır
3. ✅ Çıkan sonuçları kontrol et
4. ✅ Eksikleri tamamla
5. ✅ Model eğitimine geç

