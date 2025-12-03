# LGS Kareköklü İfadeler Tahmin Projesi

Bu depo, LGS Matematik sınavındaki kareköklü ifadeler konusuna ait geçmiş soruları toplayıp bir makine öğrenimi/LLM modeliyle yakın gelecekte çıkabilecek soru formatlarını tahmin etmeye odaklanır. Proje yapısı veri toplama, temizleme, analiz, modelleme ve değerlendirme adımlarını modüler şekilde destekleyecek biçimde kurgulandı.

## Hızlı Başlangıç

### Kurulum
1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. **OCR için Tesseract yükle:** `brew install tesseract tesseract-lang` (macOS) veya `sudo apt-get install tesseract-ocr tesseract-ocr-tur` (Linux)

### Veri Hazırlama

#### 🚀 Otomatik İndirme (Önerilen)
```bash
# MEB örnek sorularını indir (tüm yıllar)
python src/data/download_data.py --source meb --all

# Veya belirli bir yıl
python src/data/download_data.py --source meb --year 2023
```

#### 📥 Manuel İndirme
1. **MEB Resmi Sitesi:** https://odsgm.meb.gov.tr/www/ornek-sorular/icerik/listesi
2. **DersMatematik.net:** https://dersmatematik.net/lgs/
3. **Bilgenc.com:** https://www.bilgenc.com/lgs-matematik-cikmis-sorular/

İndirdiğin PDF'leri `data/raw/lgs_meb_koklu/` klasörüne koy.

**Detaylı rehber:** [`docs/HIZLI_BASLANGIC.md`](docs/HIZLI_BASLANGIC.md) | [`docs/VERI_KAYNAKLARI.md`](docs/VERI_KAYNAKLARI.md)

### İş Akışı
1. `python src/data/ingest.py --config configs/data_ingest.yaml` - Veri çıkarma
2. `python src/data/preprocess.py --input data/interim/extracted_questions.json --output data/processed/cleaned_questions.csv` - Veri temizleme
3. `python src/pipelines/train.py --config configs/train_baseline.yaml` - Model eğitimi
4. `python src/pipelines/predict.py --question "..."` - Tahmin yapma

Detaylı iş akışı için: [`docs/IS_AKISI.md`](docs/IS_AKISI.md)

## Dizin Yapısı
- `configs/`: Veri toplama, eğitim ve değerlendirme için YAML yapılandırmaları.
- `data/`: Ham (`raw`), temizlenmiş (`processed`), ara (`interim`) ve harici (`external`) veri depoları.
- `docs/`: Proje planı, literatür notları ve karar kayıtları.
- `experiments/`: Deney kayıtları, mlflow/weights&biases çıktılarına bağlantılar.
- `models/`: Kaydedilen kontrol noktaları, tokenizer dosyaları.
- `notebooks/`: Keşifsel veri analizi ve prototip çalışmalar (Jupyter).
- `reports/`: Otomatik üretilen raporlar, figürler.
- `src/`: Tüm kaynak kodu (veri hazırlama, özellik çıkarımı, modelleme, pipeline).

## Veri Kaynakları
- MEB tarafından yayımlanan resmi LGS matematik kitapçıkları (PDF).
- Özel yayınların sağladığı deneme sınavları (telif izinleri dikkate alınmalı).
- Kamuya açık soru bankaları (kareköklü ifadeler ünitesine filtrelenmiş).

`data/raw/lgs_meb_koklu/` dizininde PDF/JSON/CSV dosyalarını saklayıp `src/data/ingest.py` ile metin/şekil ayrıştırması yapılması beklenir.

## Model Yaklaşımı
- Baseline: Soru türü sınıflandırması (çoktan seçmeli şablon, açık uçlu, sayısal) için `scikit-learn` + TF-IDF.
- Gelişmiş: Türkçe matematik problemi üretimi için Türkçe destekli bir encoder-decoder (ör. `google/mt5-base`) veya LLaMA-tabanlı modelin LoRA ile ince ayarı.
- Değerlendirme: Rouge-L, BLEU, BERTScore ve konu uzmanı rubriği.

## SWOT & SMART & Videolar
- `SWOTAnalizi/`: Güçlü/zayıf yönler, fırsatlar/tehditler için dökümanlar.
- `SMARTHedefler/`: Takvimli ve ölçülebilir hedef setleri.
- `Videolar/`: Model demosu, veri toplama süreci veya eğitim anlatımları için medya dosyaları.

