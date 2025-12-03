#!/bin/bash
# Yeni veri ekleme için kolay kullanım scripti

set -e

echo "📥 Yeni Veri Ekleme Scripti"
echo "============================"
echo ""

# Yeni veri dosyasını sor
read -p "Yeni veri dosyasının yolu: " NEW_DATA

if [ ! -f "$NEW_DATA" ]; then
    echo "❌ Hata: Dosya bulunamadı: $NEW_DATA"
    exit 1
fi

# Mevcut veri seti
EXISTING="data/interim/karekok_questions.json"
OUTPUT="data/interim/karekok_questions.json"

# Yedekleme
if [ -f "$OUTPUT" ]; then
    BACKUP="${OUTPUT}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$OUTPUT" "$BACKUP"
    echo "✅ Yedek alındı: $BACKUP"
fi

# Birleştir
echo ""
echo "🔄 Veriler birleştiriliyor..."
python3 -m src.data.merge_datasets \
    --existing "$EXISTING" \
    --new "$NEW_DATA" \
    --output "$OUTPUT"

# Temizle
echo ""
echo "🧹 Veri temizleniyor..."
python3 -m src.data.preprocess \
    --input "$OUTPUT" \
    --output "data/processed/cleaned_questions.csv"

echo ""
echo "✅ Tamamlandı!"
echo "📊 Yeni veri seti: data/processed/cleaned_questions.csv"

