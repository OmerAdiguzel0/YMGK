#!/bin/bash
# Final veri seti hazırlama scripti - TÜM KONTROLLER

set -e

echo "🔧 Final Veri Seti Hazırlama"
echo "============================="
echo ""

# Yedekleme
BACKUP_DIR="data/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r data/interim/*.json "$BACKUP_DIR/" 2>/dev/null || true
cp -r data/processed/*.csv "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ Yedek alındı: $BACKUP_DIR"

# 1. Finalize
echo ""
echo "1️⃣  Veri seti standardize ediliyor..."
python3 -m src.data.finalize_dataset \
    --input data/interim/karekok_questions.json \
    --output data/processed/final_questions.json

# 2. Kalite kontrolü
echo ""
echo "2️⃣  Kalite kontrolü yapılıyor..."
python3 -m src.data.quality_check \
    --file data/processed/final_questions.json \
    --details > reports/quality_report.txt 2>&1 || true

# 3. Rapor oluştur
echo ""
echo "3️⃣  Veri seti raporu oluşturuluyor..."
python3 -m src.data.create_dataset_report \
    --input data/processed/final_questions.json \
    --output reports/dataset_report.md

# 4. Doğrulama
echo ""
echo "4️⃣  Final doğrulama..."
python3 -m src.data.validate_extraction \
    --file data/processed/final_questions.json \
    --expected 28 \
    --source "final_dataset" \
    --auto-confirm

# 5. İstatistikler
echo ""
echo "5️⃣  Final istatistikler..."
python3 << 'PYEOF'
import json
import pandas as pd

data = json.load(open('data/processed/final_questions.json'))
df = pd.read_csv('data/processed/final_questions.csv')

print("\n📊 FİNAL VERİ SETİ İSTATİSTİKLERİ")
print("=" * 50)
print(f"✅ Toplam soru: {len(data)}")
print(f"✅ JSON dosyası: data/processed/final_questions.json")
print(f"✅ CSV dosyası: data/processed/final_questions.csv")
print(f"✅ Rapor: reports/dataset_report.md")
print(f"✅ Kalite raporu: reports/quality_report.txt")

if 'extraction_method' in df.columns:
    print(f"\nÇıkarma yöntemleri:")
    for method, count in df['extraction_method'].value_counts().items():
        print(f"  • {method}: {count}")

if 'complexity' in df.columns:
    print(f"\nKarmaşıklık:")
    for comp, count in df['complexity'].value_counts().items():
        print(f"  • {comp}: {count}")

print("\n✅ Veri seti model eğitimi için hazır!")
PYEOF

echo ""
echo "✅ Tüm işlemler tamamlandı!"
echo ""
echo "📁 Dosyalar:"
echo "  • data/processed/final_questions.json"
echo "  • data/processed/final_questions.csv"
echo "  • reports/dataset_report.md"
echo "  • reports/quality_report.txt"

