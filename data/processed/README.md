# Final Veri Seti

## 📊 Genel Bilgiler

- **Toplam Soru:** 28
- **Konu:** Kareköklü İfadeler (LGS Matematik)
- **Kaynak:** karekokcikmis.pdf (LGS çıkmış sorular)
- **Oluşturulma Tarihi:** 2024-12-03

## 📁 Dosyalar

### `final_questions.json`
- **Format:** JSON (array of objects)
- **Kullanım:** Programatik erişim için
- **Encoding:** UTF-8

### `final_questions.csv`
- **Format:** CSV
- **Kullanım:** Model eğitimi, analiz için
- **Encoding:** UTF-8

## 📋 Veri Şeması

### Zorunlu Alanlar
- `question_id`: Benzersiz soru ID'si
- `question_number`: Soru numarası
- `question_text`: Soru metni (temizlenmiş)
- `source_file`: Kaynak dosya adı
- `is_koklu`: Kareköklü ifadeler sorusu mu? (true)

### Opsiyonel Alanlar
- `raw_text`: Ham soru metni
- `raw_text_cleaned`: Temizlenmiş ham metin
- `options`: Seçenekler listesi
- `correct_answer`: Doğru cevap
- `solution_text`: Çözüm açıklaması
- `extraction_method`: Çıkarma yöntemi (text/ocr/hybrid)
- `complexity`: Karmaşıklık (düşük/orta/yüksek)
- `has_image`: Görsel içerik var mı?
- `has_table`: Tablo içerik var mı?
- `has_encoding_issues`: Encoding sorunu var mı?

## ⚠️ Bilinen Sorunlar

### 1. Encoding Sorunları
- **11 soruda** `(cid:...)` karakterleri var
- **Çözüm:** `raw_text_cleaned` alanı kullanılmalı
- **Durum:** Model eğitimi için yeterli (temizlenmiş versiyonlar mevcut)

### 2. Seçenek Eksikliği
- **11 soruda** seçenek yok
- **Neden:** 
  - Parse hatası (seçenekler ayrılmamış)
  - OCR hatası
  - Açık uçlu sorular olabilir
- **Durum:** Model eğitimi için sorun değil (soru metni yeterli)

## ✅ Kalite Durumu

- **Ortalama Puan:** 72.5/100
- **Mükemmel (90+):** 0 soru
- **İyi (70-89):** 17 soru (60.7%)
- **Orta (50-69):** 11 soru (39.3%)
- **Zayıf (<50):** 0 soru

## 📊 Dağılım

### Çıkarma Yöntemleri
- **Hybrid:** 12 soru (metin + OCR birleşik)
- **Text:** 11 soru (sadece metin çıkarma)
- **OCR:** 5 soru (sadece OCR)

### Karmaşıklık
- **Yüksek:** 17 soru
- **Orta:** 7 soru
- **Düşük:** 4 soru

## 🚀 Kullanım

### Model Eğitimi İçin
```python
import pandas as pd

df = pd.read_csv('data/processed/final_questions.csv')
# question_text alanını kullan
questions = df['question_text'].tolist()
```

### Programatik Erişim
```python
import json

with open('data/processed/final_questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)
```

## 📝 Notlar

1. **Encoding:** Model eğitimi için `question_text` alanını kullan (zaten temizlenmiş)
2. **Seçenekler:** Eksik seçenekler model eğitimini etkilemez (soru üretimi için)
3. **Kalite:** Tüm sorular kullanılabilir durumda
4. **Versiyon:** v1.0 (2024-12-03)

## 🔄 Güncelleme

Yeni veri eklendiğinde:
1. `validate_and_add.sh` scripti çalıştırılır
2. Kalite kontrolü yapılır
3. Bu README güncellenir
4. Versiyon numarası artırılır

