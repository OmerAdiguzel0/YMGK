#!/usr/bin/env python3
"""karekokcikmis.pdf dosyasını işlemek için özel script."""

import sys
from pathlib import Path

# Proje root'unu path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from src.data.process_karekok_pdf import process_karekok_pdf
from rich import print

if __name__ == "__main__":
    pdf_path = Path("data/raw/lgs_meb_koklu/karekokcikmis.pdf")
    output_path = Path("data/interim/karekok_questions.json")
    
    if not pdf_path.exists():
        print(f"[red]Hata:[/red] Dosya bulunamadı: {pdf_path}")
        print(f"[yellow]Lütfen dosyayı şu konuma koyun:[/yellow] {pdf_path}")
        sys.exit(1)
    
    print(f"[bold cyan]Kareköklü İfadeler PDF İşleme Başlatılıyor...[/bold cyan]\n")
    
    process_karekok_pdf(
        pdf_path=pdf_path,
        output_path=output_path,
        use_ocr=True,  # Şekilli sorular için OCR açık
        use_text_extraction=True  # Hızlı metin çıkarma da açık
    )

