# Veri Ekleme Rehberi

## 📥 Yeni Veri Ekleme

### Yöntem 1: Otomatik Birleştirme (Önerilen)

Yeni bir PDF veya JSON dosyasından sorular çıkardıktan sonra:

```bash
# 1. Yeni veriyi çıkar (örnek: yeni bir PDF)
python3 process_karekok.py  # veya başka bir script

# 2. Yeni çıkarılan veriyi mevcut veri setine ekle
python3 -m src.data.merge_datasets \
  --existing data/interim/karekok_questions.json \
  --new data/interim/yeni_sorular.json \
  --output data/interim/karekok_questions.json
```

**Avantajlar:**
- ✅ Otomatik duplikasyon kontrolü
- ✅ Soru ID'lerini otomatik günceller
- ✅ Mevcut verileri korur

### Yöntem 2: Manuel JSON Ekleme

Yeni soruları manuel olarak hazırladıysan:

```json
[
  {
    "question_number": "29",
    "question_text": "√48 + √12 işleminin sonucu kaçtır?",
    "options": ["A) 6√3", "B) 8√3", "C) 10√3", "D) 12√3"],
    "correct_answer": "A",
    "source_file": "manuel_ekleme.json",
    "source_type": "manual",
    "is_koklu": true,
    "question_type": "yeni_nesil"
  }
]
```

Sonra birleştir:
```bash
python3 -m src.data.merge_datasets \
  --new data/raw/lgs_meb_koklu/manual/yeni_sorular.json \
  --output data/interim/karekok_questions.json
```

### Yöntem 3: Yeni PDF İşleme

Yeni bir PDF dosyası eklediysen:

1. PDF'i `data/raw/lgs_meb_koklu/` klasörüne koy
2. `process_karekok.py` scriptini çalıştır (geçici çıktı al)
3. Sonuçları mevcut veri setine ekle:

```bash
# Geçici çıktı al
python3 process_karekok.py --output data/interim/yeni_pdf_sorular.json

# Birleştir
python3 -m src.data.merge_datasets \
  --new data/interim/yeni_pdf_sorular.json \
  --output data/interim/karekok_questions.json
```

---

## 🔄 Veri Güncelleme Süreci

### Tam Süreç:

```bash
# 1. Yeni veriyi çıkar
python3 process_karekok.py

# 2. Birleştir (duplikasyon kontrolü ile)
python3 -m src.data.merge_datasets \
  --new data/interim/karekok_questions.json \
  --output data/interim/karekok_questions.json

# 3. Temizle
python3 -m src.data.preprocess \
  --input data/interim/karekok_questions.json \
  --output data/processed/cleaned_questions.csv

# 4. Model eğitimi için hazır!
```

---

## ⚙️ Duplikasyon Kontrolü

Script otomatik olarak:
- Aynı soru numarası + kaynak dosya + metin içeriğine sahip soruları tespit eder
- Duplikasyonları atlar
- Benzersiz soruları ekler

Duplikasyon kontrolünü kapatmak için:
```bash
python3 -m src.data.merge_datasets --no-deduplicate ...
```

---

## 📋 Veri Formatı Standartları

Yeni eklenen sorular şu alanları içermeli:

**Zorunlu:**
- `question_text` veya `raw_text`: Soru metni
- `source_file`: Kaynak dosya adı
- `is_koklu`: true (kareköklü ifadeler sorusu)

**Önerilen:**
- `question_number`: Soru numarası
- `options`: Seçenekler listesi
- `question_type`: "yeni_nesil" veya "klasik"
- `complexity`: "düşük", "orta", "yüksek"

**Opsiyonel:**
- `correct_answer`: Doğru cevap
- `solution_text`: Çözüm açıklaması
- `has_image`: Görsel içerik var mı?
- `has_table`: Tablo içerik var mı?

---

## 🆘 Sorun Giderme

### "ModuleNotFoundError: No module named 'src'"
```bash
export PYTHONPATH=/Users/oemiar/Desktop/YMGK:$PYTHONPATH
# veya
PYTHONPATH=/Users/oemiar/Desktop/YMGK python3 -m src.data.merge_datasets ...
```

### Duplikasyon çok fazla
- Farklı kaynaklardan aynı soruları ekliyorsan normal
- `--no-deduplicate` ile kontrolü kapatabilirsin

### Veri kayboldu
- Her zaman `--output` ile farklı bir dosyaya kaydet
- Yedek al: `cp data/interim/karekok_questions.json data/interim/karekok_questions_backup.json`

---

## 💡 İpuçları

1. **Yedekleme:** Yeni veri eklemeden önce mevcut veriyi yedekle
2. **Küçük Testler:** Önce birkaç soru ile test et
3. **Versiyonlama:** Her önemli eklemede versiyon numarası ekle
4. **Dokümantasyon:** Nereden geldiğini not al (`source_file`, `metadata`)

---

## 📊 Veri İstatistikleri

Mevcut veri setini kontrol et:
```bash
python3 -c "
import json
data = json.load(open('data/interim/karekok_questions.json'))
print(f'Toplam: {len(data)} soru')
print(f'Kaynaklar: {set(q.get(\"source_file\", \"?\") for q in data)}')
"
```

