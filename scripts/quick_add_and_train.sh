#!/bin/bash
# Hızlı veri ekleme ve prototip model eğitimi scripti
# Kullanım: ./scripts/quick_add_and_train.sh

set -e

echo "🚀 Hızlı Veri Ekleme ve Prototip Model Eğitimi"
echo "================================================"
echo ""

# Renkli çıktı için
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Mevcut soru sayısını kontrol et
echo "📊 Mevcut durum kontrol ediliyor..."
CURRENT_COUNT=$(python3 << 'EOF'
import json
try:
    data = json.load(open('data/processed/final_questions.json'))
    print(len(data))
except:
    print(0)
EOF
)

echo "  Mevcut soru sayısı: $CURRENT_COUNT"
echo ""

# 2. Yeni veri ekleme
echo "📥 Yeni veri ekleme..."
echo "  → PDF'leri data/raw/ klasörüne koyduktan sonra Enter'a basın..."
read -p "  Hazır mısınız? (y/n): " ready

if [ "$ready" != "y" ]; then
    echo "  İptal edildi."
    exit 0
fi

# Veri çıkarma ve birleştirme
echo ""
echo "  Veri çıkarılıyor ve birleştiriliyor..."
./validate_and_add.sh

# 3. Kalite iyileştirme
echo ""
echo "🔧 Kalite iyileştirme..."
./scripts/improve_quality_pipeline.sh

# 4. Final veri seti oluştur
echo ""
echo "📦 Final veri seti oluşturuluyor..."
python3 -m src.data.finalize_dataset \
  --input data/interim/karekok_questions_final_improved.json \
  --output data/processed/final_questions.json

# 5. Yeni soru sayısını kontrol et
NEW_COUNT=$(python3 << 'EOF'
import json
data = json.load(open('data/processed/final_questions.json'))
print(len(data))
EOF
)

echo ""
echo "✅ Yeni durum:"
echo "  Toplam soru sayısı: $NEW_COUNT"
echo "  Eklenen soru: $((NEW_COUNT - CURRENT_COUNT))"
echo ""

# 6. Kalite kontrolü
echo "📊 Kalite kontrolü..."
python3 -m src.data.quality_check --file data/processed/final_questions.json | head -30

# 7. 50 soru kontrolü
if [ "$NEW_COUNT" -ge 50 ]; then
    echo ""
    echo "${GREEN}✅ 50+ soru tamamlandı! Prototip model eğitimi için hazır.${NC}"
    echo ""
    
    # Model eğitimi önerisi
    read -p "  Model eğitimi başlatılsın mı? (y/n): " train
    
    if [ "$train" == "y" ]; then
        echo ""
        echo "🤖 Model eğitimi başlatılıyor..."
        python3 -m src.pipelines.train configs/train_baseline.yaml
        
        echo ""
        echo "${GREEN}✅ Model eğitimi tamamlandı!${NC}"
        echo ""
        echo "📊 Model performansı:"
        echo "  → models/baseline/ klasöründe model dosyaları oluşturuldu"
        echo "  → Detaylı rapor için: python3 -m src.pipelines.predict"
    else
        echo ""
        echo "  Model eğitimi atlandı. İstediğiniz zaman çalıştırabilirsiniz:"
        echo "  python3 -m src.pipelines.train configs/train_baseline.yaml"
    fi
else
    echo ""
    echo "${YELLOW}⚠️  Henüz 50 soru tamamlanmadı.${NC}"
    echo "  Mevcut: $NEW_COUNT soru"
    echo "  Hedef: 50 soru"
    echo "  Eksik: $((50 - NEW_COUNT)) soru"
    echo ""
    echo "  Daha fazla veri eklemek için tekrar çalıştırın:"
    echo "  ./scripts/quick_add_and_train.sh"
fi

echo ""
echo "✅ İşlem tamamlandı!"

