# Proje Planı

## 1. Amaç
- LGS Matematik sınavındaki kareköklü ifadeler konusuna ait soruları toplayıp yapılandırmak.
- Soruların türünü ve bilişsel düzeyini sınıflandırmak.
- Girdi olarak geçmiş soruları alıp benzer yeni soru şablonları üretebilen bir model geliştirmek.

## 2. Yol Haritası
1. **Veri Toplama**  
   - MEB PDF’lerinin indirilmesi, telif izinlerinin kayıt altına alınması.  
   - PDF → metin dönüştürme, şekil/simge koruması için OCR entegrasyonu.
2. **Veri Temizleme ve Etiketleme**  
   - Soru gövdeleri, seçenekler, çözüm adımları için ayrı alanlar.  
   - Taksonomi: soru tipi, zoruluk, kazanım kodu.
3. **EDA & Özellik Mühendisliği**  
   - Frekans analizleri, kök içeren sayı desenleri, kullanılan stratejiler.  
   - Embedding’ler + istatistiksel özellikler.
4. **Modelleme**  
   - Kısa vadede TF-IDF + Lojistik Regresyon, orta vadede LoRA ile LLM ince ayarı.  
   - Üretim modelleri için prompt/response çiftleri hazırlama.
5. **Değerlendirme ve Yayınlama**  
   - Otomatik metrikler + uzman rubriği.  
   - Model kartı, SWOT ve SMART çıktılarının güncellenmesi.

## 3. Teslimatlar
- Veri sözlüğü ve etiketleme kılavuzu (`docs/`).
- Eğitimli modeller (`models/`), pipeline scriptleri (`src/pipelines/`).
- SWOT, SMART, video içerikleri için taslaklar (ilgili klasörlerde).

## 4. Riskler
- Telif ve KVKK kısıtları.
- OCR doğruluğu (özellikle karmaşık kök ifadeleri).
- Veri dengesizliği (soru türlerine göre).

## 5. Başarı Ölçütleri
- En az %85 doğrulukla soru türü sınıflandırması.
- Uzman değerlendirmesinde “kabul edilebilir” olarak işaretlenen ≥ %60 yeni soru üretimi.
- Belgelenmiş veri toplama pipeline’ı ve tekrar üretilebilir eğitim süreci.

