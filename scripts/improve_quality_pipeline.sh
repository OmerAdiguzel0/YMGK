#!/bin/bash
# Veri kalitesi iyileştirme pipeline'ı
# Bu script tüm iyileştirme adımlarını sırayla çalıştırır

set -e

echo "🔧 Veri Kalitesi İyileştirme Pipeline'ı"
echo "========================================"
echo ""

# 1. Encoding sorunlu soruları yüksek kaliteli OCR ile yeniden işle
echo "📄 Adım 1: Encoding sorunlu soruları yüksek kaliteli OCR ile yeniden işleme..."
python3 -m src.data.reprocess_encoding_issues \
  --questions data/interim/karekok_questions.json \
  --pdf data/raw/lgs_meb_koklu/karekokcikmis.pdf \
  --output data/interim/karekok_questions_reprocessed.json

echo ""
echo "✅ Adım 1 tamamlandı"
echo ""

# 2. Genel kalite iyileştirme
echo "🔧 Adım 2: Genel kalite iyileştirme..."
python3 -m src.data.improve_quality \
  --input data/interim/karekok_questions_reprocessed.json \
  --output data/interim/karekok_questions_final_improved.json

echo ""
echo "✅ Adım 2 tamamlandı"
echo ""

# 3. Final veri seti oluştur
echo "📦 Adım 3: Final veri seti oluşturma..."
python3 -m src.data.finalize_dataset \
  --input data/interim/karekok_questions_final_improved.json \
  --output data/processed/final_questions.json

echo ""
echo "✅ Adım 3 tamamlandı"
echo ""

# 4. Kalite kontrolü
echo "📊 Adım 4: Kalite kontrolü..."
python3 -m src.data.quality_check \
  --file data/processed/final_questions.json

echo ""
echo "✅ Tüm adımlar tamamlandı!"
echo ""
echo "📈 Final kalite raporu:"
python3 -m src.data.quality_check --file data/processed/final_questions.json | head -20

