# Soru Kalitesi Kontrolü Rehberi

## 🎯 Amaç

Soruların doğru okunup okunmadığını, yarım alınıp alınmadığını, saçmalanıp saçmalanmadığını kontrol etmek.

---

## 🔍 Otomatik Kontroller

Sistem şu kontrolleri yapar:

### 1. **Soru Metni Kontrolü**
- ✅ Soru metni var mı?
- ✅ Yeterince uzun mu? (min 20 karakter)
- ✅ Çok uzun mu? (max 5000 karakter - birleşik olabilir)

### 2. **Encoding Kontrolü**
- ✅ `(cid:...)` karakterleri var mı?
- ✅ Temizlenmiş versiyon mevcut mu?

### 3. **Seçenek Kontrolü**
- ✅ Seçenekler var mı?
- ✅ 4 seçenek var mı? (normal LGS formatı)

### 4. **Format Kontrolü**
- ✅ Soru işareti var mı?
- ✅ Soru numarası geçerli mi?

### 5. **İçerik Kontrolü**
- ✅ Kareköklü ifade var mı? (konu filtresi)
- ✅ Anlamsız karakterler var mı?
- ✅ Metin yarım kalmış mı?

### 6. **Tekrar Kontrolü**
- ✅ Çok fazla tekrarlanan kelime var mı? (parse hatası)

---

## 📊 Kalite Puanlama

- **Mükemmel (90-100)**: Hiç sorun yok
- **İyi (70-89)**: Küçük uyarılar var
- **Orta (50-69)**: Bazı sorunlar var
- **Zayıf (<50)**: Ciddi sorunlar var

---

## 🚀 Kullanım

### Yöntem 1: Otomatik Rapor

```bash
python3 -m src.data.quality_check --file data/interim/karekok_questions.json --details
```

**Çıktı:**
- Toplam soru sayısı
- Kalite dağılımı (mükemmel/iyi/orta/zayıf)
- Ortalama puan
- Problemli sorular listesi

### Yöntem 2: İnteraktif İnceleme

```bash
python3 -m src.data.quality_check --file data/interim/karekok_questions.json --interactive
```

**Özellikler:**
- Problemli soruları tek tek gösterir
- Her soruyu onaylayabilirsin
- Düzeltilmesi gerekenleri işaretleyebilirsin

### Yöntem 3: Kolay Script

```bash
./review_questions.sh
```

Script:
1. Kalite raporu gösterir
2. İnteraktif inceleme önerir
3. Problemli soruları gösterir

---

## 📋 Veri Ekleme Sürecinde

Yeni veri eklerken otomatik kontrol yapılır:

```bash
./validate_and_add.sh
```

**Süreç:**
1. ✅ Soru sayısı kontrolü
2. ✅ Kalite kontrolü
3. ✅ Problemli sorular gösterilir
4. ✅ Onay istenir
5. ✅ Veriler eklenir

---

## ⚠️ Yaygın Sorunlar ve Çözümler

### Sorun 1: Encoding Hatası
**Belirti:** `(cid:...)` karakterleri  
**Çözüm:** OCR ile tekrar çıkar veya `raw_text_cleaned` kullan

### Sorun 2: Yarım Kalmış Metin
**Belirti:** Metin `...` veya `---` ile bitiyor  
**Çözüm:** PDF'den tekrar çıkar, sayfa sınırlarını kontrol et

### Sorun 3: Birleşik Sorular
**Belirti:** Çok uzun metin (5000+ karakter)  
**Çözüm:** Parse algoritmasını iyileştir veya manuel ayır

### Sorun 4: Eksik Seçenekler
**Belirti:** 4'ten az seçenek  
**Çözüm:** OCR ile tekrar çıkar veya manuel ekle

### Sorun 5: Tekrarlanan Kelimeler
**Belirti:** Aynı kelimeler çok fazla tekrar ediyor  
**Çözüm:** Parse hatası olabilir, PDF'den tekrar çıkar

---

## 💡 İpuçları

1. **İlk Veri Ekleme:** Mutlaka kalite kontrolü yap
2. **Problemli Sorular:** İnteraktif inceleme ile kontrol et
3. **Düşük Puan:** %20'den fazla zayıf soru varsa dikkat et
4. **OCR Kullan:** Encoding sorunları için OCR genelde daha iyi
5. **Manuel Kontrol:** Şüpheli soruları manuel kontrol et

---

## 📊 Örnek Çıktı

```
📊 SORU KALİTE RAPORU
============================================================
              Özet               
┏━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━┓
┃ Kategori     ┃ Sayı ┃ Yüzde ┃
┡━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━┩
│ Toplam Soru  │ 28   │ 100%  │
│ Mükemmel     │ 0    │ 0.0%  │
│ İyi          │ 17   │ 60.7% │
│ Orta         │ 11   │ 39.3% │
│ Zayıf        │ 0    │ 0.0%  │
└──────────────┴──────┴───────┘

Ortalama Kalite Puanı: 72.5/100
```

---

## ✅ Sonuç

Kalite kontrolü ile:
- ✅ Soruların doğru okunduğunu doğrularsın
- ✅ Yarım kalmış soruları tespit edersin
- ✅ Saçmalanmış metinleri bulursun
- ✅ Model eğitimi için güvenilir veri sağlarsın

