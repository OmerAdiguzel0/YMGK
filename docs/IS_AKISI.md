# İş Akışı ve Veri İhtiyaçları

## Genel Bakış

Bu proje, LGS Matematik sınavındaki **kareköklü ifadeler** konusuna ait soruları toplayıp, yapay zeka modeliyle gelecekte çıkabilecek soru formatlarını tahmin etmeyi amaçlar.

---

## 📋 İş Akışı Aşamaları

### **AŞAMA 1: Veri Toplama ve Hazırlama** 🔍

#### 1.1. Veri Kaynakları
- **MEB Resmi LGS Kitapçıkları** (PDF formatında)
  - Yıllar: 2018-2024 arası
  - Sadece Matematik kitapçıkları
  - Kareköklü ifadeler konusuna ait sorular filtrelenecek
  
- **MEB Dökümanları** (PDF/Word formatında)
  - Örnek sorular, deneme sınavları
  - Konu anlatım kitaplarından örnekler
  
- **Görsel Dosyalar** (PNG, JPG, PDF içindeki görseller)
  - Soru görselleri
  - Şekil içeren sorular
  - OCR ile metin çıkarımı yapılacak

#### 1.2. Veri Formatı Gereksinimleri

**Sen bana şunları sağlamalısın:**

1. **PDF Dosyaları** → `data/raw/lgs_meb_koklu/` klasörüne
   - Dosya adlandırma: `LGS_2023_Matematik.pdf`, `LGS_2024_Matematik.pdf` gibi
   - Veya: `MEB_Ornek_Sorular_2024.pdf` gibi

2. **Görsel Dosyalar** → `data/raw/lgs_meb_koklu/images/` klasörüne
   - Dosya adlandırma: `soru_001.jpg`, `soru_002.png` gibi
   - Veya: `LGS_2023_Soru_15.jpg` gibi

3. **Manuel Olarak Hazırlanmış JSON/CSV** (opsiyonel)
   - Eğer soruları zaten yapılandırılmış formatta hazırladıysan:
   - `data/raw/lgs_meb_koklu/manual/*.json` veya `*.csv`

#### 1.3. Veri Yapısı (Hedef Format)

Her soru şu formatta olmalı:
```json
{
  "question_id": "LGS_2023_MAT_15",
  "question_text": "√48 + √12 işleminin sonucu kaçtır?",
  "options": ["A) 6√3", "B) 8√3", "C) 10√3", "D) 12√3"],
  "correct_answer": "A",
  "solution_text": "√48 = 4√3, √12 = 2√3, toplam = 6√3",
  "difficulty": "orta",
  "question_type": "işlem",
  "year": 2023,
  "source": "MEB_LGS_2023",
  "has_image": false,
  "image_path": null,
  "topic": "kareköklü_ifadeler"
}
```

---

### **AŞAMA 2: Veri Çıkarma (Extraction)** 🔧

#### 2.1. PDF'den Metin Çıkarma
- `pdfplumber` ve `PyPDF2` kütüphaneleri kullanılacak
- Soru numaraları, seçenekler, cevaplar otomatik ayrıştırılacak
- Tablolar ve şekiller korunacak

#### 2.2. Görsellerden OCR ile Metin Çıkarma
- `pytesseract` (Tesseract OCR) kullanılacak
- Türkçe dil desteği aktif
- Matematiksel semboller için özel işleme

#### 2.3. Soru Filtreleme
- Sadece **kareköklü ifadeler** konusuna ait sorular seçilecek
- Anahtar kelimeler: "kök", "√", "kareköklü", "irrasyonel sayı" vb.

**Bu aşamada senin yapman gereken:**
- PDF ve görsel dosyalarını `data/raw/lgs_meb_koklu/` klasörüne koymak
- Ben scriptleri hazırlayacağım, sen sadece verileri sağlayacaksın

---

### **AŞAMA 3: Veri Temizleme ve Yapılandırma** 🧹

#### 3.1. Otomatik Temizlik
- Boşluklar, özel karakterler normalize edilecek
- Tekrarlanan sorular tespit edilip çıkarılacak
- Eksik alanlar (seçenek, cevap vb.) işaretlenecek

#### 3.2. Manuel Kontrol Gereken Durumlar
- OCR hataları (özellikle matematiksel semboller)
- Görsel sorularda eksik bilgiler
- Çözüm adımlarının eksik olması

**Bu aşamada senin yapman gereken:**
- Otomatik işlemlerden sonra çıkan hatalı kayıtları kontrol etmek
- Eksik bilgileri tamamlamak (opsiyonel)

---

### **AŞAMA 4: Veri Etiketleme ve Sınıflandırma** 🏷️

#### 4.1. Soru Türleri
- **İşlem Soruları**: Toplama, çıkarma, çarpma, bölme
- **Karşılaştırma Soruları**: Hangi sayı daha büyük/küçük
- **Sadeleştirme Soruları**: Kök içinden çıkarma
- **Problem Soruları**: Gerçek hayat senaryoları
- **Şekil İçeren Sorular**: Geometri ile ilişkili

#### 4.2. Zorluk Seviyeleri
- **Kolay**: Temel işlemler
- **Orta**: Birkaç adımlı işlemler
- **Zor**: Karmaşık problemler

**Bu aşamada senin yapman gereken:**
- İlk 20-30 soruyu manuel etiketleyerek örnek oluşturmak (opsiyonel)
- Model otomatik etiketleme yapabilir, ama senin kontrolün önemli

---

### **AŞAMA 5: Özellik Çıkarımı (Feature Engineering)** 📊

#### 5.1. Metin Özellikleri
- TF-IDF vektörleri
- Türkçe BERT embedding'leri
- Soru uzunluğu, kelime sayısı

#### 5.2. Matematiksel Özellikler
- Kök içindeki sayılar
- İşlem türleri (toplama, çıkarma, çarpma, bölme)
- Kullanılan formüller

**Bu aşama tamamen otomatik, senin bir şey yapmana gerek yok.**

---

### **AŞAMA 6: Model Eğitimi** 🤖

#### 6.1. Baseline Model
- TF-IDF + Logistic Regression
- Soru türü sınıflandırması
- Hızlı prototip için

#### 6.2. Gelişmiş Model
- Türkçe BERT veya mT5 tabanlı model
- Soru üretimi için fine-tuning
- LoRA ile verimli eğitim

**Bu aşama tamamen otomatik, senin bir şey yapmana gerek yok.**

---

### **AŞAMA 7: Değerlendirme ve Tahmin** ✅

#### 7.1. Model Performansı
- Doğruluk metrikleri
- Soru türü sınıflandırma başarısı
- Üretilen soruların kalitesi

#### 7.2. Tahmin Yapma
- Yeni soru formatları önerme
- Benzer soru bulma
- Zorluk tahmini

---

## 🎯 ŞİMDİ NE YAPMALIYIZ?

### **İlk Adım: Veri Toplama**

**Sen bana şunları sağlamalısın:**

1. ✅ **PDF Dosyaları** (MEB LGS kitapçıkları)
   - `data/raw/lgs_meb_koklu/` klasörüne koy
   - Dosya adları: `LGS_2023_Matematik.pdf`, `LGS_2024_Matematik.pdf` gibi

2. ✅ **Görsel Dosyalar** (soru görselleri)
   - `data/raw/lgs_meb_koklu/images/` klasörüne koy
   - PNG, JPG formatında

3. ✅ **Manuel JSON/CSV** (eğer varsa)
   - `data/raw/lgs_meb_koklu/manual/` klasörüne koy

### **Ben Ne Yapacağım:**

1. ✅ PDF'den metin çıkarma scriptlerini yazacağım
2. ✅ OCR pipeline'ını kuracağım
3. ✅ Soru ayrıştırma ve yapılandırma kodlarını hazırlayacağım
4. ✅ Veri temizleme ve ön işleme adımlarını otomatikleştireceğim

---

## 📝 Notlar

- **Minimum Veri**: En az 100 soru hedefliyoruz (SMART hedefler)
- **Veri Kalitesi**: Her sorunun en azından soru metni, seçenekler ve doğru cevabı olmalı
- **Telif Hakları**: Sadece kamuya açık MEB dökümanlarını kullanıyoruz
- **İlerleme**: Her aşamada seninle koordinasyon halinde ilerleyeceğiz

---

## 🔄 Sonraki Adımlar

1. **Sen verileri topla ve klasörlere koy**
2. **Bana haber ver, ben scriptleri çalıştırayım**
3. **Çıkan sonuçları birlikte kontrol edelim**
4. **Eksikleri tamamlayıp bir sonraki aşamaya geçelim**

