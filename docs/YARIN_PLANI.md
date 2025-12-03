# Yarın İçin Plan: 22 Soru Ekleme ve Prototip Hazırlığı

## 🎯 Hedef
- **Mevcut:** 28 soru
- **Eklenecek:** 22 soru
- **Toplam:** 50 soru
- **Amaç:** Prototip model eğitimi

## 📋 Adım Adım Plan

### 1. Yeni Soruları Bulma ve Ekleme

#### A. Veri Kaynakları
- MEB LGS çıkmış sorular (PDF)
- Deneme sınavları (PDF)
- Online soru bankaları (PDF/JSON)
- **Önemli:** Sadece kareköklü ifadeler konusundan sorular

#### B. Veri Ekleme Süreci
```bash
# 1. Yeni PDF'leri data/raw/ klasörüne koy
# 2. Veri çıkarma ve kalite kontrolü
./validate_and_add.sh

# Veya manuel:
python3 -m src.data.ingest  # Veri çıkarma
python3 -m src.data.merge_datasets  # Birleştirme
python3 -m src.data.preprocess  # Temizleme
python3 -m src.data.quality_check  # Kalite kontrolü
```

### 2. Kalite Kontrolü

#### Kontrol Edilecekler
- ✅ Toplam soru sayısı: 50 olmalı
- ✅ Kalite puanı: 80+ olmalı
- ✅ Encoding sorunları: Minimum olmalı
- ✅ Seçenek eksikliği: %20'den az olmalı

#### Kalite Kontrol Komutları
```bash
# Kalite raporu
python3 -m src.data.quality_check --file data/processed/final_questions.json --details

# Soru sayısı kontrolü
python3 << 'EOF'
import json
data = json.load(open('data/processed/final_questions.json'))
print(f"Toplam soru: {len(data)}")
EOF
```

### 3. Prototip Model Eğitimi

#### Model Eğitimi Adımları
```bash
# 1. Veri hazırlığı
python3 -m src.data.finalize_dataset \
  --input data/interim/karekok_questions_final_improved.json \
  --output data/processed/final_questions.json

# 2. Model eğitimi
python3 -m src.pipelines.train configs/train_baseline.yaml

# 3. Model değerlendirmesi
python3 -m src.pipelines.predict --model models/baseline/baseline_classifier.joblib
```

### 4. Prototip Raporu

#### Raporlanacaklar
- Veri seti özeti (50 soru)
- Kalite metrikleri
- Model performansı
- Sonraki adımlar

## ⚠️ Dikkat Edilmesi Gerekenler

### Veri Ekleme Sırasında
1. **Kalite Kontrolü:** Her yeni veri eklemeden sonra kalite kontrolü yap
2. **Duplikasyon:** Aynı soru birden fazla eklenmemeli
3. **Format Tutarlılığı:** Tüm sorular aynı formatta olmalı
4. **Encoding:** Yeni sorularda encoding sorunu olmamalı

### Model Eğitimi Öncesi
1. **Veri Bölünmesi:** Train/Validation/Test split kontrolü
2. **Özellik Mühendisliği:** Gerekli özellikler hazır mı?
3. **Model Konfigürasyonu:** configs/train_baseline.yaml kontrolü

## 📊 Beklenen Sonuçlar

### Veri Seti
- **Toplam Soru:** 50
- **Kalite Puanı:** 80-85/100
- **Encoding Sorunu:** <5 soru
- **Seçenek Eksikliği:** <10 soru

### Model Performansı
- **Beklenen Başarı:** ~%70-75
- **Validation F1:** ~0.70-0.75
- **Test Accuracy:** ~%70-75

## 🚀 Hızlı Başlangıç Komutları

### Tüm Süreci Tek Seferde Çalıştır
```bash
# 1. Yeni veri ekle (PDF'leri data/raw/ klasörüne koyduktan sonra)
./validate_and_add.sh

# 2. Kalite iyileştirme
./scripts/improve_quality_pipeline.sh

# 3. Final veri seti oluştur
python3 -m src.data.finalize_dataset \
  --input data/interim/karekok_questions_final_improved.json \
  --output data/processed/final_questions.json

# 4. Kalite kontrolü
python3 -m src.data.quality_check --file data/processed/final_questions.json

# 5. Model eğitimi
python3 -m src.pipelines.train configs/train_baseline.yaml
```

## 📝 İleride 150+ Soru İçin Notlar

### Veri Toplama Stratejisi
1. **Sürekli Veri Ekleme:** Her hafta yeni sorular ekle
2. **Otomatik Kalite Kontrolü:** Her eklemede otomatik kontrol
3. **Veri Çeşitliliği:** Farklı yıllar, zorluk seviyeleri, soru tipleri
4. **Veri Birleştirme:** Tüm kaynaklardan soruları birleştir

### Model İyileştirme
1. **Daha Fazla Veri:** 150+ soru ile model performansı artacak
2. **Model Güncelleme:** Yeni verilerle modeli yeniden eğit
3. **Performans Takibi:** Veri miktarı arttıkça performansı ölç

## ✅ Kontrol Listesi

### Veri Ekleme Öncesi
- [ ] Yeni PDF'ler hazır
- [ ] Veri kaynakları belirlendi
- [ ] Kareköklü ifadeler filtresi hazır

### Veri Ekleme Sırasında
- [ ] Veri çıkarma tamamlandı
- [ ] Kalite kontrolü yapıldı
- [ ] Duplikasyon kontrolü yapıldı
- [ ] Veri birleştirme yapıldı

### Prototip Öncesi
- [ ] 50 soru tamamlandı
- [ ] Kalite puanı 80+ oldu
- [ ] Final veri seti oluşturuldu
- [ ] Model konfigürasyonu hazır

### Prototip Sonrası
- [ ] Model eğitildi
- [ ] Performans ölçüldü
- [ ] Rapor hazırlandı
- [ ] Sonraki adımlar planlandı

