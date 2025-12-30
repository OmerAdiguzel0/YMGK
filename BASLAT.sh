#!/bin/bash
# Streamlit arayüzünü başlatma scripti

cd "$(dirname "$0")"

# Virtual environment'ı aktif et
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment bulunamadı!"
    echo "Lütfen önce virtual environment oluşturun:"
    echo "  python3 -m venv .venv"
    exit 1
fi

# Streamlit'i kontrol et
if ! command -v streamlit &> /dev/null; then
    echo "📦 Streamlit yükleniyor..."
    pip install streamlit joblib
fi

# Arayüzü başlat
echo "🚀 Arayüz başlatılıyor..."
streamlit run app.py

