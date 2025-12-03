# İleride 150+ Soru İçin Plan

## 🎯 Uzun Vadeli Hedef
- **Hedef:** 150+ soru
- **Amaç:** Production-ready model
- **Beklenen Performans:** %75-80 başarı

## 📊 Mevcut Durum → Hedef

| Aşama | Soru Sayısı | Kalite | Model Başarısı | Durum |
|-------|-------------|--------|----------------|-------|
| Şu An | 28 | 84.8/100 | ~%67.8 | ✅ Kalite yeterli |
| Prototip | 50 | 80-85/100 | ~%70-75 | 🎯 Yarın hedef |
| Production | 150+ | 85+/100 | ~%75-80 | 🚀 İleride hedef |

## 📋 Veri Toplama Stratejisi

### 1. Veri Kaynakları
- ✅ MEB LGS çıkmış sorular (PDF)
- ✅ Deneme sınavları (PDF)
- ✅ Online soru bankaları (PDF/JSON)
- ✅ Öğretmen kaynakları (PDF)
- ✅ Yayın evi soru bankaları (PDF)

### 2. Veri Ekleme Süreci

#### Otomatik Süreç
```bash
# Her yeni veri eklemede
./validate_and_add.sh

# Kalite kontrolü
python3 -m src.data.quality_check --file data/processed/final_questions.json

# Kalite iyileştirme (gerekirse)
./scripts/improve_quality_pipeline.sh
```

#### Manuel Süreç
1. PDF'leri `data/raw/` klasörüne koy
2. Veri çıkarma: `python3 -m src.data.ingest`
3. Birleştirme: `python3 -m src.data.merge_datasets`
4. Temizleme: `python3 -m src.data.preprocess`
5. Kalite kontrolü: `python3 -m src.data.quality_check`

### 3. Veri Çeşitliliği

#### Yıl Dağılımı
- 2018-2024 LGS soruları
- Farklı yıllardan örnekler

#### Zorluk Seviyesi
- Kolay: %30
- Orta: %50
- Zor: %20

#### Soru Tipleri
- Klasik sorular
- Yeni nesil sorular
- Görsel içerikli sorular
- Tablo/grafik içerikli sorular

## 🔄 Sürekli İyileştirme

### Haftalık Rutin
1. **Veri Ekleme:** Her hafta 10-20 yeni soru ekle
2. **Kalite Kontrolü:** Her eklemede otomatik kontrol
3. **Model Güncelleme:** Ayda bir modeli yeniden eğit
4. **Performans Takibi:** Model performansını ölç ve kaydet

### Aylık Rutin
1. **Veri Seti Raporu:** Aylık veri seti özeti
2. **Model Performansı:** Model başarısı raporu
3. **İyileştirme Planı:** Sonraki ay için plan

## 📈 Beklenen İyileşmeler

### Veri Miktarı Artışı
- **50 soru:** ~%70-75 başarı
- **100 soru:** ~%75-78 başarı
- **150+ soru:** ~%75-80 başarı (hedef)

### Kalite İyileştirmeleri
- Encoding sorunları: <2%
- Seçenek eksikliği: <10%
- Ortalama kalite: 85+/100

## 🛠️ Teknik Altyapı

### Otomatik Pipeline
```bash
# Veri ekleme → Kalite kontrolü → Model güncelleme
./scripts/automated_data_pipeline.sh
```

### Monitoring
- Veri seti büyüklüğü takibi
- Kalite metrikleri takibi
- Model performansı takibi

### Backup
- Düzenli veri yedekleme
- Model versiyonlama
- Rapor arşivleme

## 📝 Checklist: 150+ Soru İçin

### Veri Toplama
- [ ] 10+ farklı kaynak belirlendi
- [ ] Otomatik veri çıkarma pipeline'ı hazır
- [ ] Kalite kontrol sistemi kuruldu
- [ ] Veri birleştirme sistemi hazır

### Model Eğitimi
- [ ] Model konfigürasyonu hazır
- [ ] Eğitim pipeline'ı hazır
- [ ] Değerlendirme metrikleri belirlendi
- [ ] Model versiyonlama sistemi kuruldu

### Monitoring
- [ ] Veri seti takip sistemi kuruldu
- [ ] Model performansı takip sistemi kuruldu
- [ ] Raporlama sistemi hazır

## 🎯 Başarı Kriterleri

### Veri Seti
- ✅ 150+ soru
- ✅ 85+ kalite puanı
- ✅ <5% encoding sorunu
- ✅ <10% seçenek eksikliği

### Model Performansı
- ✅ %75-80 başarı
- ✅ F1 score: 0.75-0.80
- ✅ Validation accuracy: %75-80

## 🚀 Sonraki Adımlar

1. **Kısa Vadeli (1-2 Hafta)**
   - 50 soru ile prototip model
   - Performans ölçümü
   - İyileştirme planı

2. **Orta Vadeli (1-2 Ay)**
   - 100+ soru toplama
   - Model güncelleme
   - Performans iyileştirme

3. **Uzun Vadeli (3+ Ay)**
   - 150+ soru hedefi
   - Production-ready model
   - %75-80 başarı hedefi

