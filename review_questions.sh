#!/bin/bash
# Soruları manuel olarak inceleme scripti

set -e

echo "🔍 Soru İnceleme ve Doğrulama"
echo "=============================="
echo ""

# Dosya yolu
read -p "İncelenecek soru dosyası (varsayılan: data/interim/karekok_questions.json): " FILE
FILE=${FILE:-data/interim/karekok_questions.json}

if [ ! -f "$FILE" ]; then
    echo "❌ Hata: Dosya bulunamadı: $FILE"
    exit 1
fi

echo ""
echo "📊 Kalite raporu oluşturuluyor..."
python3 -m src.data.quality_check --file "$FILE" --details

echo ""
read -p "Problemli soruları interaktif olarak incelemek ister misiniz? (E/h): " INTERACTIVE

if [[ $INTERACTIVE =~ ^[EeYy] ]]; then
    echo ""
    echo "🔍 İnteraktif inceleme başlatılıyor..."
    python3 -m src.data.quality_check --file "$FILE" --interactive
fi

echo ""
echo "✅ İnceleme tamamlandı!"

