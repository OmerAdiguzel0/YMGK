# 🌐 Web Arayüzü Kullanım Kılavuzu

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. Arayüzü Başlat
```bash
streamlit run app.py
```

Tarayıcınızda otomatik olarak açılacak (genellikle `http://localhost:8501`)

## 📋 Özellikler

### 🎲 Soru Üret
- **Üretilecek Soru Sayısı**: 1-20 arası seçim
- **Üretim Yöntemi**: 
  - `template`: Şablon tabanlı üretim
  - `hybrid`: Şablon + LLM kombinasyonu
- **Çıktı**: Üretilen sorular JSON formatında indirilebilir

### 🔍 Benzer Soruları Bul
- Soru metni girerek benzer soruları bulma
- Benzerlik skorları ile sıralama
- Kaynak dosya ve soru numarası bilgisi

### 📚 Veri Seti
- Toplam soru sayısı
- Kaynaklara göre dağılım grafiği
- Örnek soruları görüntüleme

## 🎨 Arayüz Özellikleri

- **Modern ve Kullanıcı Dostu**: Temiz ve anlaşılır tasarım
- **Responsive**: Farklı ekran boyutlarına uyumlu
- **Hızlı**: Cache mekanizması ile optimize edilmiş
- **İndirilebilir**: Üretilen sorular JSON formatında indirilebilir

## ⚙️ Yapılandırma

Arayüz otomatik olarak şu dosyaları arar:
- `models/baseline/templates.json` - Şablonlar
- `models/baseline/questions.json` - Sorular
- `models/baseline/vectorizer.joblib` - Benzerlik modeli

## 🐛 Sorun Giderme

### Model dosyaları bulunamıyor
```bash
# Önce modeli eğitin
python3 -m src.pipelines.generate_questions --train --questions models/baseline/questions.json
```

### Port zaten kullanılıyor
```bash
streamlit run app.py --server.port 8502
```

## 📝 Notlar

- İlk kullanımda model dosyaları cache'lenecektir
- Büyük veri setlerinde arama biraz zaman alabilir
- Üretilen soruları kontrol etmeyi unutmayın!

