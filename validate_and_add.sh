#!/bin/bash
# Veri doğrulama ve ekleme scripti (güvenli sürüm)

set -e

echo "🔍 Veri Doğrulama ve Ekleme"
echo "============================"
echo ""

# Yeni veri dosyasını sor
read -p "Yeni veri dosyasının yolu: " NEW_DATA

if [ ! -f "$NEW_DATA" ]; then
    echo "❌ Hata: Dosya bulunamadı: $NEW_DATA"
    exit 1
fi

# Beklenen soru sayısını sor
read -p "Beklenen soru sayısı (boş bırakabilirsin): " EXPECTED_COUNT

# Mevcut veri seti
EXISTING="data/interim/karekok_questions.json"
OUTPUT="data/interim/karekok_questions.json"

# 1. DOĞRULAMA (Soru Sayısı)
echo ""
echo "🔍 Veri doğrulanıyor (soru sayısı)..."
VALIDATE_CMD="python3 -m src.data.validate_extraction --file \"$NEW_DATA\" --source \"$(basename $NEW_DATA)\" --auto-confirm"

if [ ! -z "$EXPECTED_COUNT" ]; then
    VALIDATE_CMD="$VALIDATE_CMD --expected $EXPECTED_COUNT"
fi

eval $VALIDATE_CMD
VALIDATE_EXIT=$?

if [ $VALIDATE_EXIT -ne 0 ]; then
    echo ""
    echo "❌ Doğrulama başarısız! Lütfen verileri kontrol edin."
    exit 1
fi

# 2. KALİTE KONTROLÜ
echo ""
echo "🔍 Soru kalitesi kontrol ediliyor..."
QUALITY_EXIT=0
python3 -m src.data.quality_check --file "$NEW_DATA" --details || QUALITY_EXIT=$?

if [ $QUALITY_EXIT -ne 0 ]; then
    echo ""
    echo "⚠️  Kalite kontrolünde sorunlar bulundu!"
    read -p "Yine de devam etmek istiyor musunuz? (E/h): " CONTINUE
    if [[ ! $CONTINUE =~ ^[EeYy] ]]; then
        echo "İşlem iptal edildi."
        exit 1
    fi
fi

# Kullanıcı onayı
echo ""
read -p "Bu verileri mevcut veri setine eklemek istiyor musunuz? (E/h): " CONFIRM

if [[ ! $CONFIRM =~ ^[EeYy] ]]; then
    echo "⚠️  İşlem iptal edildi."
    exit 0
fi

# 2. YEDEKLEME
if [ -f "$OUTPUT" ]; then
    BACKUP="${OUTPUT}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$OUTPUT" "$BACKUP"
    echo ""
    echo "✅ Yedek alındı: $BACKUP"
fi

# 3. BİRLEŞTİRME
echo ""
echo "🔄 Veriler birleştiriliyor..."
python3 -m src.data.merge_datasets \
    --existing "$EXISTING" \
    --new "$NEW_DATA" \
    --output "$OUTPUT"

# 4. TEMİZLEME
echo ""
echo "🧹 Veri temizleniyor..."
python3 -m src.data.preprocess \
    --input "$OUTPUT" \
    --output "data/processed/cleaned_questions.csv"

# 5. SON DOĞRULAMA
echo ""
echo "🔍 Final doğrulama..."
python3 -c "
import json
data = json.load(open('$OUTPUT'))
print(f'✅ Toplam soru sayısı: {len(data)}')
"

echo ""
echo "✅ Tamamlandı!"
echo "📊 Yeni veri seti: data/processed/cleaned_questions.csv"

